import logging

from djpsa.halo import models
from djpsa.halo import sync
from djpsa.halo.records import api
from djpsa.sync.sync import InvalidObjectException
from djpsa.utils import redis_lock

logger = logging.getLogger(__name__)

# Moving a ticket rewrites the project's whole milestone list, so two moves on
# one project must not interleave: the second would post an array it read
# before the first landed, silently undoing it. Keyed per project, since that
# array is the only thing being contended.
MILESTONE_LOCK = 'halo_project_milestones_{}'
# Long enough to cover a GET + POST cycle if the holder dies mid-write, short
# enough that a dead worker doesn't hold the project for long.
MILESTONE_LOCK_LIFETIME = 60
# Someone is waiting on this, so give up rather than queue indefinitely.
MILESTONE_LOCK_ACQUIRE_TIMEOUT = 20


class MilestoneSynchronizer(sync.ResponseKeyMixin, sync.HaloSynchronizer):
    """
    Sync Halo project milestones.

    The Milestone endpoint answers ``Allow: GET`` — it returns every milestone
    in the tenant in one paginated pass, with no server-side filtering, so this
    always does a full fetch. Writes go through the project ticket instead;
    see :meth:`update_dependencies` and :meth:`set_ticket_milestone`.

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

    def update_dependencies(self, project_id, dependencies):
        """
        Set the milestone each of a project's milestones depends on, in Halo.

        ``dependencies`` maps child milestone id -> parent milestone id, with
        ``None`` to clear. The whole mapping is applied in one request, so a
        set of edits either all land in Halo or none do.

        Halo has no writable milestone endpoint: the only way in is to POST the
        project ticket with its **whole** ``milestones`` array, which it treats
        as a full replacement — anything left out is deleted, and a field left
        off a milestone that is included gets blanked. So this re-reads the
        array from Halo and posts back exactly what it returned, touching only
        the named milestones' ``milestone_dependencies``. Rebuilding the array
        from local rows instead would silently discard whatever changed in Halo
        since the last sync.
        """
        if not dependencies:
            return

        client = api.TicketAPI()

        detail = client.request(
            'GET', endpoint_url=client._format_endpoint(project_id))
        remote = detail.get('milestones') or []

        remote_ids = {row.get('id') for row in remote}
        missing = set(dependencies) - remote_ids
        if missing:
            # Posting the array now would delete the milestones Halo does have.
            raise InvalidObjectException(
                'Milestone(s) {} are no longer on project {} in HaloPSA; '
                'refusing to write the milestone list.'.format(
                    sorted(missing), project_id))

        for row in remote:
            if row.get('id') in dependencies:
                parent_id = dependencies[row['id']]
                row['milestone_dependencies'] = (
                    [{'id': parent_id}] if parent_id else []
                )

        client.update(project_id, {'milestones': remote})
        logger.info(
            'Set milestone dependencies %s on project %s',
            dependencies, project_id)

    def set_ticket_milestone(self, project_id, ticket_id, milestone_id):
        """
        Move a ticket into one of its project's milestones, in Halo.

        ``milestone_id`` of ``None`` takes the ticket out of every milestone.

        The ticket's own ``milestone_id`` is read-only — Halo answers 201 and
        leaves it unchanged — and so is the ``tickets`` array. The way in is
        ``tickets_list`` on the project's milestone rows, through the same
        whole-array replacement :meth:`update_dependencies` uses, with the same
        refusal when the target is no longer on the project.

        Membership is many-to-many in Halo, so this drops the ticket from every
        one of the project's milestones before adding it to the target.
        Appending alone would leave it in both, and ``Ticket.milestone`` is a
        single FK.
        """
        ticket = models.Ticket.objects.filter(id=ticket_id).first()
        if ticket is None:
            raise InvalidObjectException(
                'Ticket {} does not exist.'.format(ticket_id))
        if ticket.project_id != project_id:
            # Halo does not check this: it accepts a ticket into another
            # project's milestone and leaves the ticket reporting a milestone
            # on a project it is not part of, while its old membership stands.
            raise InvalidObjectException(
                'Ticket {} is not on project {}.'.format(
                    ticket_id, project_id))

        with redis_lock(MILESTONE_LOCK.format(project_id),
                        MILESTONE_LOCK_LIFETIME,
                        MILESTONE_LOCK_ACQUIRE_TIMEOUT):
            client = api.TicketAPI()

            detail = client.request(
                'GET', endpoint_url=client._format_endpoint(project_id))
            remote = detail.get('milestones') or []

            target = None
            if milestone_id:
                target = next(
                    (row for row in remote if row.get('id') == milestone_id),
                    None)
                if target is None:
                    # Posting the array now would delete the milestones Halo
                    # does have.
                    raise InvalidObjectException(
                        'Milestone {} is no longer on project {} in HaloPSA; '
                        'refusing to write the milestone list.'.format(
                            milestone_id, project_id))

            for row in remote:
                row['tickets_list'] = [
                    t for t in (row.get('tickets_list') or [])
                    if t.get('id') != ticket_id
                ]

            if target is not None:
                # Halo fills the rest of the row in from the ticket itself, so
                # the id is all it needs — and a ticket that is in no milestone
                # yet has no row anywhere to copy.
                target['tickets_list'].append({'id': ticket_id})

            client.update(project_id, {'milestones': remote})

            # Only once Halo has accepted it. Its `tickets` array follows the
            # `tickets_list` write on its own, so the next sync agrees.
            models.Ticket.objects.filter(id=ticket_id).update(
                milestone_id=milestone_id)

        logger.info(
            'Set ticket %s to milestone %s on project %s',
            ticket_id, milestone_id, project_id)
