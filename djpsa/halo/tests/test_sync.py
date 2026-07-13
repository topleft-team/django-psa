from unittest import TestCase, mock
from unittest.mock import MagicMock, patch
from django.utils import timezone
from dateutil.parser import parse
from djpsa.halo.sync import empty_date_parser, ResponseKeyMixin
from djpsa.halo import models
from djpsa.halo.records.ticket.sync import TicketSynchronizer
from djpsa.halo.records.ticket.model import ItilRequestType
from djpsa.halo.records.agent.sync import AgentSynchronizer


class TestEmptyDateParser(TestCase):

    def test_valid_date(self):
        date_str = "2023-10-10T10:00:00"
        expected_date = timezone.make_aware(parse(date_str), timezone.utc)
        self.assertEqual(empty_date_parser(date_str), expected_date)

    def test_empty_date(self):
        date_str = "1900-01-01T00:00:00"
        self.assertIsNone(empty_date_parser(date_str))

    def test_none_date(self):
        self.assertIsNone(empty_date_parser(None))

    def test_edge_case_date(self):
        date_str = "1980-01-01T00:00:00"
        self.assertIsNone(empty_date_parser(date_str))

    def test_above_edge_case_date(self):
        date_str = "1981-01-01T00:00:00"
        expected_date = timezone.make_aware(parse(date_str), timezone.utc)
        self.assertEqual(empty_date_parser(date_str), expected_date)


class TestResponseKeyMixin(TestCase):

    def setUp(self):
        class TestClass(ResponseKeyMixin):
            response_key = 'data'

        self.test_instance = TestClass()

    def test_unpack_records(self):
        response = {'data': [{'id': 1, 'name': 'Test'}]}
        expected_records = [{'id': 1, 'name': 'Test'}]
        self.assertEqual(
            self.test_instance._unpack_records(response), expected_records)


class TestTicketSynchronizerClosedTasks(TestCase):
    """The Halo sync must include an open project's closed tasks regardless of
    age, so its closed/total child counts stay accurate for consumers."""

    def _make_sync(self, full=True):
        # Avoid hitting the real Halo API or the DB during construction.
        with patch.object(TicketSynchronizer, 'client_class', MagicMock()), \
                patch(
                    'djpsa.halo.records.ticket.sync.models.FieldInfoReference'
                ) as field_info:
            field_info.objects.values_list.return_value = []
            return TicketSynchronizer(full=full)

    def test_try_validate_keeps_old_closed_task_during_tasks_pass(self):
        sync = self._make_sync()
        old_closed = (
            timezone.now() - timezone.timedelta(days=365)
        ).strftime('%Y-%m-%dT%H:%M:%S')
        record = {'dateclosed': old_closed}

        # Outside the closed-tasks pass, a long-closed ticket is rejected by
        # the keep_closed_days cutoff (default 1 day).
        sync._syncing_all_closed_tasks = False
        self.assertFalse(sync._try_validate(record))

        # During the closed-project-tasks pass it is kept regardless of age.
        sync._syncing_all_closed_tasks = True
        self.assertTrue(sync._try_validate(record))

    def test_post_sync_operations_syncs_open_projects_closed_tasks(self):
        sync = self._make_sync(full=True)

        # Record the flag's value at each fetch so we can prove the cutoff is
        # only lifted for the closed-project-tasks pass.
        flag_states = []

        def record_fetch(results):
            flag_states.append(sync._syncing_all_closed_tasks)
            return results

        with patch(
                'djpsa.halo.records.ticket.sync.models.Ticket'
        ) as ticket_model, \
                patch.object(sync, 'fetch_records', side_effect=record_fetch):
            ticket_model.projects_only.filter.return_value \
                .values_list.return_value = [101, 202]
            sync._post_sync_operations(MagicMock())

        # Only open projects drive the closed-tasks pass.
        ticket_model.projects_only.filter.assert_called_once_with(
            date_closed__isnull=True)

        # One recently-closed pass (any type, cutoff on), then one pass per
        # open project (cutoff lifted).
        self.assertEqual(flag_states, [False, True, True])

        # The closed-project-tasks pass scopes to project tasks and drops the
        # keep_closed_days window.
        sync.client.add_condition.assert_any_call(
            {'itil_requesttype': ItilRequestType.TASKS.value})
        sync.client.remove_condition.assert_any_call('lastupdatefromdate')

        # Each open project is fetched by its own parent_id, then cleared so
        # the ids don't accumulate across iterations.
        sync.client.add_condition.assert_any_call({'parent_id': 101})
        sync.client.add_condition.assert_any_call({'parent_id': 202})
        sync.client.remove_condition.assert_any_call('parent_id')

        # The flag is reset once the pass completes.
        self.assertFalse(sync._syncing_all_closed_tasks)

    def test_post_sync_operations_noop_on_partial_sync(self):
        sync = self._make_sync(full=False)

        with patch.object(sync, 'fetch_records') as fetch_records:
            sync._post_sync_operations(MagicMock())

        # Partial syncs keep open_only and do no closed passes.
        fetch_records.assert_not_called()
        self.assertFalse(sync._syncing_all_closed_tasks)


class TestAgentSynchronizer(TestCase):
    """The agent cost rate (Halo `costprice`) feeds project-margin costing."""

    def _synchronizer(self):
        # Stub the API client so construction needs no Halo credentials.
        with mock.patch.object(AgentSynchronizer, 'client_class'):
            return AgentSynchronizer()

    def test_assigns_cost_price_from_costprice(self):
        instance = models.Agent()
        self._synchronizer()._assign_field_data(instance, {
            'id': 6, 'name': 'Amir Said', 'costprice': 30.0,
        })
        self.assertEqual(instance.id, 6)
        self.assertEqual(instance.name, 'Amir Said')
        self.assertEqual(instance.cost_price, 30.0)

    def test_cost_price_absent_stays_none(self):
        # No cost visibility on the API role -> field omitted -> stays None.
        instance = models.Agent()
        self._synchronizer()._assign_field_data(instance, {
            'id': 7, 'name': 'No Cost',
        })
        self.assertIsNone(instance.cost_price)
