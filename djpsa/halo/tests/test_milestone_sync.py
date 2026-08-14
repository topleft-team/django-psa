from unittest import mock

from django.test import TestCase

from djpsa.api.exceptions import APIError
from djpsa.halo import models
from djpsa.halo.records.milestone.sync import MilestoneSynchronizer
from djpsa.halo.records.ticket.model import ItilRequestType
from djpsa.sync.sync import InvalidObjectException

PROJECT = ItilRequestType.PROJECTS.value


def milestone_payload(milestone_id, project_id, name='Plan', sequence=1,
                      tickets=(), dependencies=()):
    """One row as the Halo Milestone endpoint returns it."""
    return {
        'id': milestone_id,
        'ticket_id': project_id,
        'name': name,
        'sequence': sequence,
        'state': 2,
        'start_date': '2026-03-01T09:00:00',
        'target_date': '2026-03-31T17:00:00',
        'milestone_dependencies': [{'id': p} for p in dependencies],
        'dependencies': [
            {'id': 100 + i, 'child': milestone_id, 'parent': parent}
            for i, parent in enumerate(dependencies)
        ],
        'tickets': [
            {'id': 200 + i, 'milestone_id': milestone_id, 'ticket_id': t,
             'ticket_name': str(t)}
            for i, t in enumerate(tickets)
        ],
        # Halo returns the member tickets twice, in its search-result shape as
        # well. This is the one it accepts writes on.
        'tickets_list': [
            {'id': t, 'idsummary': '{} - Task'.format(t), 'table': 1,
             'use': 'ticket'}
            for t in tickets
        ],
    }


class MilestoneSynchronizerTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.status = models.Status.objects.create(id=1, name='In Progress')
        self.project = models.Ticket.objects.create(
            id=500, summary='Migration', status=self.status,
            itil_request_type=PROJECT)

    def _synchronizer(self):
        # Stub the API client so construction needs no Halo credentials.
        with mock.patch.object(MilestoneSynchronizer, 'client_class'):
            return MilestoneSynchronizer()

    def _task(self, ticket_id, milestone=None):
        return models.Ticket.objects.create(
            id=ticket_id, summary='Task {}'.format(ticket_id),
            status=self.status, project=self.project, milestone=milestone)

    def _milestone(self, milestone_id, sequence=1, name='Plan'):
        return models.Milestone.objects.create(
            id=milestone_id, ticket=self.project, name=name,
            sequence=sequence, state=2)

    # --- validation ------------------------------------------------------

    def test_template_milestones_are_skipped(self):
        """Halo returns project *templates* under a negative ticket_id. They
        have no local project, so they must not be synced at all."""
        sync = self._synchronizer()
        self.assertFalse(sync._try_validate({'ticket_id': -33}))
        self.assertFalse(sync._try_validate({'ticket_id': 0}))
        self.assertTrue(sync._try_validate({'ticket_id': 500}))

    # --- field mapping ---------------------------------------------------

    def test_assign_field_data_maps_the_payload(self):
        sync = self._synchronizer()
        instance = models.Milestone()

        sync._assign_field_data(
            instance, milestone_payload(1, 500, name='Plan', sequence=3))

        self.assertEqual(instance.id, 1)
        self.assertEqual(instance.name, 'Plan')
        self.assertEqual(instance.sequence, 3)
        self.assertEqual(instance.state, 2)
        self.assertEqual(instance.ticket_id, 500)
        self.assertEqual(instance.start_date.isoformat(), '2026-03-01')
        self.assertEqual(instance.target_date.isoformat(), '2026-03-31')

    def test_assign_field_data_buffers_links_and_edges(self):
        """Both reference milestones that may not exist yet, so they are
        applied in a second pass rather than inline."""
        sync = self._synchronizer()

        sync._assign_field_data(
            models.Milestone(),
            milestone_payload(2, 500, tickets=(11, 12), dependencies=(1,)))

        self.assertEqual(sync._ticket_links, {2: {11, 12}})
        self.assertEqual(sync._edges, {2: {1}})

    # --- reconciliation --------------------------------------------------

    def test_post_sync_links_tickets_to_their_milestone(self):
        sync = self._synchronizer()
        plan = self._milestone(1)
        self._task(11)
        self._task(12)

        sync._ticket_links = {1: {11, 12}}
        sync._edges = {1: set()}
        sync._post_sync_operations(mock.Mock())

        self.assertEqual(
            set(models.Ticket.objects.filter(milestone=plan)
                .values_list('id', flat=True)),
            {11, 12})

    def test_post_sync_clears_a_ticket_that_left_its_milestone(self):
        sync = self._synchronizer()
        plan = self._milestone(1)
        stayed = self._task(11, milestone=plan)
        left = self._task(12, milestone=plan)

        sync._ticket_links = {1: {stayed.id}}
        sync._edges = {1: set()}
        sync._post_sync_operations(mock.Mock())

        left.refresh_from_db()
        stayed.refresh_from_db()
        self.assertIsNone(left.milestone_id)
        self.assertEqual(stayed.milestone_id, 1)

    def test_post_sync_creates_dependency_edges(self):
        sync = self._synchronizer()
        self._milestone(1, sequence=1, name='Plan')
        self._milestone(2, sequence=2, name='Build')

        sync._ticket_links = {1: set(), 2: set()}
        sync._edges = {1: set(), 2: {1}}
        sync._post_sync_operations(mock.Mock())

        self.assertEqual(
            list(models.MilestoneDependency.objects
                 .values_list('child_id', 'parent_id')),
            [(2, 1)])

    def test_post_sync_removes_an_edge_dropped_in_halo(self):
        sync = self._synchronizer()
        plan = self._milestone(1, sequence=1)
        build = self._milestone(2, sequence=2, name='Build')
        models.MilestoneDependency.objects.create(child=build, parent=plan)

        sync._ticket_links = {1: set(), 2: set()}
        sync._edges = {1: set(), 2: set()}
        sync._post_sync_operations(mock.Mock())

        self.assertFalse(models.MilestoneDependency.objects.exists())

    def test_post_sync_ignores_an_edge_to_an_unsynced_milestone(self):
        """A parent that was skipped (a template, or a project we don't sync)
        has nothing local to point at."""
        sync = self._synchronizer()
        self._milestone(2, sequence=2, name='Build')

        sync._ticket_links = {2: set()}
        sync._edges = {2: {999}}
        sync._post_sync_operations(mock.Mock())

        self.assertFalse(models.MilestoneDependency.objects.exists())

    def test_post_sync_is_a_no_op_when_nothing_was_fetched(self):
        """An empty response must not be read as "Halo deleted everything"."""
        sync = self._synchronizer()
        plan = self._milestone(1)
        build = self._milestone(2, sequence=2, name='Build')
        models.MilestoneDependency.objects.create(child=build, parent=plan)
        self._task(11, milestone=plan)

        sync._post_sync_operations(mock.Mock())

        self.assertTrue(models.MilestoneDependency.objects.exists())
        self.assertEqual(
            models.Ticket.objects.filter(milestone=plan).count(), 1)

    # --- writing back ----------------------------------------------------

    def _patched_ticket_api(self, remote_milestones):
        client = mock.MagicMock()
        client.request.return_value = {'milestones': remote_milestones}
        client._format_endpoint.return_value = 'https://halo/api/Tickets/500'
        return client

    def test_update_dependencies_posts_the_whole_milestone_list(self):
        """Halo treats the list as a full replacement, so every milestone must
        go back — dropping one would delete it."""
        sync = self._synchronizer()
        remote = [
            milestone_payload(1, 500, name='Plan', sequence=1),
            milestone_payload(2, 500, name='Build', sequence=2),
        ]
        client = self._patched_ticket_api(remote)

        with mock.patch(
                'djpsa.halo.records.milestone.sync.api.TicketAPI',
                return_value=client):
            sync.update_dependencies(500, {2: 1})

        client.update.assert_called_once()
        project_id, data = client.update.call_args[0]
        self.assertEqual(project_id, 500)
        sent = data['milestones']
        self.assertEqual([m['id'] for m in sent], [1, 2])
        # Only the target milestone's dependency changed; everything else is
        # posted back exactly as Halo returned it.
        self.assertEqual(sent[1]['milestone_dependencies'], [{'id': 1}])
        self.assertEqual(sent[0]['milestone_dependencies'], [])
        self.assertEqual(sent[0]['name'], 'Plan')
        self.assertEqual(sent[1]['tickets'], remote[1]['tickets'])

    def test_update_dependencies_applies_every_edge_in_one_request(self):
        """A set of edits lands together or not at all — one POST, so Halo
        can't end up with half the graph."""
        sync = self._synchronizer()
        client = self._patched_ticket_api([
            milestone_payload(1, 500, name='Plan', sequence=1),
            milestone_payload(2, 500, name='Build', sequence=2),
            milestone_payload(3, 500, name='Verify', sequence=3,
                              dependencies=(2,)),
        ])

        with mock.patch(
                'djpsa.halo.records.milestone.sync.api.TicketAPI',
                return_value=client):
            sync.update_dependencies(500, {2: 1, 3: None})

        client.update.assert_called_once()
        sent = client.update.call_args[0][1]['milestones']
        self.assertEqual(sent[1]['milestone_dependencies'], [{'id': 1}])
        self.assertEqual(sent[2]['milestone_dependencies'], [])

    def test_update_dependencies_clears_with_none(self):
        sync = self._synchronizer()
        client = self._patched_ticket_api([
            milestone_payload(2, 500, name='Build', sequence=2,
                              dependencies=(1,)),
        ])

        with mock.patch(
                'djpsa.halo.records.milestone.sync.api.TicketAPI',
                return_value=client):
            sync.update_dependencies(500, {2: None})

        sent = client.update.call_args[0][1]['milestones']
        self.assertEqual(sent[0]['milestone_dependencies'], [])

    def test_update_dependencies_is_a_no_op_when_empty(self):
        sync = self._synchronizer()
        client = self._patched_ticket_api([])

        with mock.patch(
                'djpsa.halo.records.milestone.sync.api.TicketAPI',
                return_value=client):
            sync.update_dependencies(500, {})

        client.request.assert_not_called()
        client.update.assert_not_called()

    def test_update_dependencies_refuses_when_a_milestone_is_gone(self):
        """Posting the list we just read would delete the milestones Halo
        still has, so bail out instead — including when only one of several
        targets has vanished."""
        sync = self._synchronizer()
        client = self._patched_ticket_api([
            milestone_payload(1, 500, name='Plan', sequence=1),
            milestone_payload(2, 500, name='Build', sequence=2),
        ])

        with mock.patch(
                'djpsa.halo.records.milestone.sync.api.TicketAPI',
                return_value=client):
            with self.assertRaises(InvalidObjectException):
                sync.update_dependencies(500, {2: 1, 99: 1})

        client.update.assert_not_called()

    def test_update_dependencies_refuses_when_halo_returns_no_milestones(self):
        sync = self._synchronizer()
        client = self._patched_ticket_api([])

        with mock.patch(
                'djpsa.halo.records.milestone.sync.api.TicketAPI',
                return_value=client):
            with self.assertRaises(InvalidObjectException):
                sync.update_dependencies(500, {2: 1})

        client.update.assert_not_called()

    # --- moving a ticket between milestones -------------------------------

    def _set_milestone(self, client, *args, **kwargs):
        """Run set_ticket_milestone against a stubbed API and lock."""
        sync = self._synchronizer()
        with mock.patch(
                'djpsa.halo.records.milestone.sync.api.TicketAPI',
                return_value=client):
            with mock.patch(
                    'djpsa.halo.records.milestone.sync.redis_lock') as lock:
                sync.set_ticket_milestone(*args, **kwargs)
        return lock

    def test_set_ticket_milestone_moves_the_ticket(self):
        """Out of the source, into the target, and the local row follows."""
        plan = self._milestone(1)
        self._milestone(2, sequence=2, name='Build')
        task = self._task(11, milestone=plan)
        client = self._patched_ticket_api([
            milestone_payload(1, 500, name='Plan', sequence=1,
                              tickets=(11, 12)),
            milestone_payload(2, 500, name='Build', sequence=2, tickets=(13,)),
        ])

        self._set_milestone(client, 500, 11, 2)

        sent = client.update.call_args[0][1]['milestones']
        self.assertEqual(
            [t['id'] for t in sent[0]['tickets_list']], [12])
        self.assertEqual(
            [t['id'] for t in sent[1]['tickets_list']], [13, 11])
        task.refresh_from_db()
        self.assertEqual(task.milestone_id, 2)

    def test_set_ticket_milestone_adds_only_the_id(self):
        """Halo fills the rest of the row in, and a ticket in no milestone has
        no row to copy."""
        self._milestone(1)
        self._task(11)
        client = self._patched_ticket_api([
            milestone_payload(1, 500, name='Plan', sequence=1),
        ])

        self._set_milestone(client, 500, 11, 1)

        sent = client.update.call_args[0][1]['milestones']
        self.assertEqual(sent[0]['tickets_list'], [{'id': 11}])

    def test_set_ticket_milestone_posts_the_whole_milestone_list(self):
        """Halo replaces the array, so every milestone goes back untouched
        apart from the membership that moved."""
        plan = self._milestone(1)
        self._milestone(2, sequence=2, name='Build')
        self._task(11, milestone=plan)
        remote = [
            milestone_payload(1, 500, name='Plan', sequence=1, tickets=(11,)),
            milestone_payload(2, 500, name='Build', sequence=2,
                              dependencies=(1,)),
        ]
        client = self._patched_ticket_api(remote)

        self._set_milestone(client, 500, 11, 2)

        client.update.assert_called_once()
        project_id, data = client.update.call_args[0]
        self.assertEqual(project_id, 500)
        sent = data['milestones']
        self.assertEqual([m['id'] for m in sent], [1, 2])
        self.assertEqual(sent[0]['name'], 'Plan')
        self.assertEqual(sent[1]['milestone_dependencies'], [{'id': 1}])

    def test_set_ticket_milestone_leaves_the_tickets_array_alone(self):
        """Halo recomputes `tickets` from the `tickets_list` write itself."""
        plan = self._milestone(1)
        self._task(11, milestone=plan)
        remote = [milestone_payload(1, 500, name='Plan', sequence=1,
                                    tickets=(11,))]
        untouched = [dict(row) for row in remote[0]['tickets']]
        client = self._patched_ticket_api(remote)

        self._set_milestone(client, 500, 11, None)

        sent = client.update.call_args[0][1]['milestones']
        self.assertEqual(sent[0]['tickets'], untouched)

    def test_set_ticket_milestone_clears_with_none(self):
        """A ticket can hold no milestone at all."""
        plan = self._milestone(1)
        task = self._task(11, milestone=plan)
        client = self._patched_ticket_api([
            milestone_payload(1, 500, name='Plan', sequence=1,
                              tickets=(11, 12)),
        ])

        self._set_milestone(client, 500, 11, None)

        sent = client.update.call_args[0][1]['milestones']
        self.assertEqual([t['id'] for t in sent[0]['tickets_list']], [12])
        task.refresh_from_db()
        self.assertIsNone(task.milestone_id)

    def test_set_ticket_milestone_drops_every_other_membership(self):
        """Halo membership is many-to-many; the local FK is not. Appending
        without removing would leave the ticket in both."""
        plan = self._milestone(1)
        self._milestone(2, sequence=2, name='Build')
        self._milestone(3, sequence=3, name='Verify')
        self._task(11, milestone=plan)
        client = self._patched_ticket_api([
            milestone_payload(1, 500, name='Plan', sequence=1, tickets=(11,)),
            milestone_payload(2, 500, name='Build', sequence=2, tickets=(11,)),
            milestone_payload(3, 500, name='Verify', sequence=3),
        ])

        self._set_milestone(client, 500, 11, 3)

        sent = client.update.call_args[0][1]['milestones']
        self.assertEqual(sent[0]['tickets_list'], [])
        self.assertEqual(sent[1]['tickets_list'], [])
        self.assertEqual([t['id'] for t in sent[2]['tickets_list']], [11])

    def test_set_ticket_milestone_holds_a_lock_on_the_project(self):
        """Two moves on one project must not interleave — the second would
        post an array it read before the first landed."""
        self._milestone(1)
        self._task(11)
        client = self._patched_ticket_api([
            milestone_payload(1, 500, name='Plan', sequence=1),
        ])

        lock = self._set_milestone(client, 500, 11, 1)

        lock.assert_called_once()
        self.assertEqual(lock.call_args[0][0], 'halo_project_milestones_500')

    def test_set_ticket_milestone_refuses_when_the_milestone_is_gone(self):
        """Posting the list we just read would delete the milestones Halo
        still has."""
        plan = self._milestone(1)
        task = self._task(11, milestone=plan)
        client = self._patched_ticket_api([
            milestone_payload(1, 500, name='Plan', sequence=1, tickets=(11,)),
        ])

        with self.assertRaises(InvalidObjectException):
            self._set_milestone(client, 500, 11, 99)

        client.update.assert_not_called()
        task.refresh_from_db()
        self.assertEqual(task.milestone_id, 1)

    def test_set_ticket_milestone_refuses_a_ticket_on_another_project(self):
        """Halo accepts this and leaves the ticket claiming a milestone on a
        project it is not part of, its old membership still standing."""
        other = models.Ticket.objects.create(
            id=600, summary='Other project', status=self.status,
            itil_request_type=PROJECT)
        models.Ticket.objects.create(
            id=11, summary='Task 11', status=self.status, project=other)
        self._milestone(1)
        client = self._patched_ticket_api([
            milestone_payload(1, 500, name='Plan', sequence=1),
        ])

        with self.assertRaises(InvalidObjectException):
            self._set_milestone(client, 500, 11, 1)

        client.request.assert_not_called()
        client.update.assert_not_called()

    def test_set_ticket_milestone_refuses_an_unknown_ticket(self):
        client = self._patched_ticket_api([
            milestone_payload(1, 500, name='Plan', sequence=1),
        ])

        with self.assertRaises(InvalidObjectException):
            self._set_milestone(client, 500, 999, 1)

        client.update.assert_not_called()

    def test_set_ticket_milestone_keeps_the_local_row_when_halo_rejects(self):
        """TopLeft must not claim a move HaloPSA refused."""
        plan = self._milestone(1)
        self._milestone(2, sequence=2, name='Build')
        task = self._task(11, milestone=plan)
        client = self._patched_ticket_api([
            milestone_payload(1, 500, name='Plan', sequence=1, tickets=(11,)),
            milestone_payload(2, 500, name='Build', sequence=2),
        ])
        client.update.side_effect = APIError('Halo said no')

        with self.assertRaises(APIError):
            self._set_milestone(client, 500, 11, 2)

        task.refresh_from_db()
        self.assertEqual(task.milestone_id, 1)
