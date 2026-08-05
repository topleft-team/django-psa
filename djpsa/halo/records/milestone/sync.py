import logging

from djpsa.halo import models
from djpsa.halo import sync
from djpsa.halo.records import api
from djpsa.sync.sync import InvalidObjectException

logger = logging.getLogger(__name__)


class MilestoneSynchronizer(sync.ResponseKeyMixin, sync.HaloSynchronizer):
    """
    Sync Halo project milestones.

    The Milestone endpoint answers ``Allow: GET`` — it returns every milestone
    in the tenant in one paginated pass, with no server-side filtering, so this
    always does a full fetch. Writes go through the project ticket instead;
    see :meth:`update_dependency`.

    Two things ride along in the milestone payload rather than on the ticket:
    the member-ticket join rows (``tickets``) and the milestone-to-milestone
    dependency edges (``dependencies``). Both reference milestones that may not
    be persisted yet when their row is processed, so they are buffered during
    the fetch and reconciled in a second pass.
    """
    response_key = 'data'
    model_class = models.MilestoneTracker
    client_class = api.MilestoneAPI

    related_meta = {
        'ticket_id': (models.Ticket, 'ticket'),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # milestone id -> set of member ticket ids
        self._ticket_links = {}
        # milestone id -> set of parent milestone ids
        self._edges = {}

    def _try_validate(self, record):
        # Project templates carry milestones too, under a negative ticket_id.
        # They have no corresponding local project, so skip them outright
        # rather than letting each one fail the FK lookup.
        return record.get('ticket_id', 0) > 0

    def _assign_field_data(self, instance, json_data):
        instance.id = json_data.get('id')
        instance.name = json_data.get('name')
        instance.sequence = json_data.get('sequence')
        instance.state = json_data.get('state')
        instance.start_date = \
            sync.parse_date_from_api(json_data.get('start_date'))
        instance.target_date = \
            sync.parse_date_from_api(json_data.get('target_date'))

        self.set_relations(instance, json_data)

        self._ticket_links[instance.id] = {
            row['ticket_id'] for row in json_data.get('tickets') or []
            if row.get('ticket_id', 0) > 0
        }
        self._edges[instance.id] = {
            edge['parent'] for edge in json_data.get('dependencies') or []
            if edge.get('parent')
        }

    def _post_sync_operations(self, results):
        if not self._ticket_links and not self._edges:
            # Nothing came back. Reconciling now would clear every local link
            # and edge on the strength of an empty response.
            return results

        self._reconcile_ticket_links()
        self._reconcile_dependencies()
        return results

    def _reconcile_ticket_links(self):
        """Point each ticket at its milestone, and drop links Halo dropped."""
        seen = set(self._ticket_links)
        desired = {}
        for milestone_id, ticket_ids in self._ticket_links.items():
            for ticket_id in ticket_ids:
                desired[ticket_id] = milestone_id

        # A ticket that left one of the milestones we just saw.
        models.Ticket.objects \
            .filter(milestone_id__in=seen) \
            .exclude(id__in=desired) \
            .update(milestone=None)

        by_milestone = {}
        for ticket_id, milestone_id in desired.items():
            by_milestone.setdefault(milestone_id, []).append(ticket_id)

        for milestone_id, ticket_ids in by_milestone.items():
            models.Ticket.objects \
                .filter(id__in=ticket_ids) \
                .exclude(milestone_id=milestone_id) \
                .update(milestone_id=milestone_id)

    def _reconcile_dependencies(self):
        """Bring MilestoneDependency in line with the edges Halo reported."""
        stored = set(
            models.Milestone.objects.values_list('id', flat=True))

        desired = set()
        for child_id, parent_ids in self._edges.items():
            if child_id not in stored:
                continue
            for parent_id in parent_ids:
                # A parent whose milestone was skipped (template, or a project
                # we don't sync) has nothing local to point at.
                if parent_id in stored:
                    desired.add((child_id, parent_id))

        existing = set(
            models.MilestoneDependency.objects
            .filter(child_id__in=self._edges)
            .values_list('child_id', 'parent_id'))

        stale = existing - desired
        for child_id, parent_id in stale:
            models.MilestoneDependency.objects.filter(
                child_id=child_id, parent_id=parent_id).delete()

        models.MilestoneDependency.objects.bulk_create(
            [
                models.MilestoneDependency(
                    child_id=child_id, parent_id=parent_id)
                for child_id, parent_id in desired - existing
            ],
            ignore_conflicts=True,
        )

    def update_dependency(self, milestone, parent_milestone_id):
        """
        Set (or clear, with ``parent_milestone_id=None``) the milestone this
        one depends on, in Halo.

        Halo has no writable milestone endpoint: the only way in is to POST the
        project ticket with its **whole** ``milestones`` array, which it treats
        as a full replacement — anything left out is deleted, and a field left
        off a milestone that is included gets blanked. So this re-reads the
        array from Halo and posts back exactly what it returned, touching only
        the one milestone's ``milestone_dependencies``. Rebuilding the array
        from local rows instead would silently discard whatever changed in Halo
        since the last sync.
        """
        client = api.TicketAPI()
        project_id = milestone.ticket_id

        detail = client.request(
            'GET', endpoint_url=client._format_endpoint(project_id))
        remote = detail.get('milestones') or []

        if not any(row.get('id') == milestone.id for row in remote):
            # Posting the array now would delete the milestones Halo does have.
            raise InvalidObjectException(
                'Milestone {} is no longer on project {} in HaloPSA; '
                'refusing to write the milestone list.'.format(
                    milestone.id, project_id))

        for row in remote:
            if row.get('id') == milestone.id:
                row['milestone_dependencies'] = (
                    [{'id': parent_milestone_id}] if parent_milestone_id
                    else []
                )

        client.update(project_id, {'milestones': remote})
        logger.info(
            'Set milestone %s dependency to %s on project %s',
            milestone.id, parent_milestone_id, project_id)
