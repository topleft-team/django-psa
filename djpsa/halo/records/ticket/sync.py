from typing import Any, List

from django.utils import timezone
from dateutil.parser import parse

from djpsa.halo import models
from djpsa.halo.records import api
from djpsa.halo.sync import ResponseKeyMixin, empty_date_parser
from djpsa.halo import sync
from djpsa.halo.records.agent.api import UNASSIGNED_AGENT_ID


class TicketSynchronizer(ResponseKeyMixin,
                         sync.CreateMixin,
                         sync.UpdateMixin,
                         sync.DeleteMixin,
                         sync.HaloSynchronizer,
                         ):
    response_key = 'tickets'
    model_class = models.TicketTracker
    client_class = api.TicketAPI
    last_updated_field = 'lastupdatefromdate'

    related_meta = {
        'client_id': (models.Client, 'client'),
        'status_id': (models.Status, 'status'),
        'priority_id': (models.Priority, 'priority'),
        'agent_id': (models.Agent, 'agent'),
        'sla_id': (models.SLA, 'sla'),
        'user_id': (models.HaloUser, 'user'),
        'site_id': (models.Site, 'site'),
        'tickettype_id': (models.TicketType, 'type'),
        'parent_id': (models.Ticket, 'project'),
    }

    def __init__(self,
                 full: bool = False,
                 conditions: List = None,
                 *args: Any,
                 **kwargs: Any):
        super().__init__(full, conditions, *args, **kwargs)

        if full:
            self.client.add_condition({
                'open_only': True,
            })

    def _assign_field_data(self, instance, json_data):
        instance.id = json_data.get('id')
        instance.summary = json_data.get('summary')
        instance.details = json_data.get('details')
        instance.last_action_date = timezone.make_aware(
            parse(json_data.get('lastactiondate')), timezone.utc)
        instance.last_update = timezone.make_aware(
            parse(json_data.get('last_update')), timezone.utc)
        instance.user_email = json_data.get('useremail')
        instance.reported_by = json_data.get('reportedby')
        instance.end_user_status = json_data.get('enduserstatus')
        instance.category_1 = json_data.get('category1')
        instance.category_2 = json_data.get('category2')
        instance.category_3 = json_data.get('category3')
        instance.category_4 = json_data.get('category4')
        instance.inactive = json_data.get('inactive', False)
        instance.sla_response_state = json_data.get('sla_response_state')
        instance.sla_hold_time = json_data.get('sla_hold_time')
        instance.impact = json_data.get('impact')
        instance.flagged = json_data.get('flagged', False)
        instance.on_hold = json_data.get('onhold', False)
        instance.project_time_actual = json_data.get('projecttimeactual')
        instance.project_money_actual = json_data.get('projectmoneyactual')
        instance.cost = json_data.get('cost')
        instance.estimate = json_data.get('estimate')
        instance.estimated_days = json_data.get('estimateddays')
        instance.exclude_from_slas = json_data.get('excludefromslas', False)
        instance.team = json_data.get('team')
        instance.reviewed = json_data.get('reviewed', False)
        instance.read = json_data.get('read', False)
        instance.use = json_data.get('use')
        instance.email_to_list = json_data.get('emailtolist')
        instance.urgency = json_data.get('urgency')
        instance.service_status_note = json_data.get('servicestatusnote')
        instance.ticket_tags = json_data.get('tickettags')
        instance.appointment_type = json_data.get('appointment_type')
        instance.impact_level = json_data.get('impactlevel')

        date_occurred = json_data.get('dateoccurred')
        instance.date_occurred = empty_date_parser(date_occurred)

        respond_by_date = json_data.get('respondbydate')
        instance.respond_by_date = empty_date_parser(respond_by_date)

        fix_by_date = json_data.get('fixbydate')
        instance.fix_by_date = empty_date_parser(fix_by_date)

        date_assigned = json_data.get('dateassigned')
        instance.date_assigned = empty_date_parser(date_assigned)

        response_date = json_data.get('responsedate')
        instance.response_date = empty_date_parser(response_date)

        deadline_date = json_data.get('deadlinedate')
        instance.deadline_date = empty_date_parser(deadline_date)

        start_date = json_data.get('startdate')
        instance.start_date = empty_date_parser(start_date)

        if instance.start_date:
            # Don't set time if start date is empty.
            instance.start_date = instance.start_date.replace(
                hour=parse(json_data.get('starttime')).hour,
                minute=parse(json_data.get('starttime')).minute,
                second=parse(json_data.get('starttime')).second
            )

        target_date = json_data.get('targetdate')
        instance.target_date = empty_date_parser(target_date)

        if instance.target_date:
            # Don't set time if target date is empty.
            instance.target_date = instance.target_date.replace(
                hour=parse(json_data.get('targettime')).hour,
                minute=parse(json_data.get('targettime')).minute,
                second=parse(json_data.get('targettime')).second
            )

        last_incoming_email_date = json_data.get('lastincomingemaildate')
        instance.last_incoming_email_date = \
            empty_date_parser(last_incoming_email_date)

        self.set_relations(instance, json_data)
        if instance.agent_id == UNASSIGNED_AGENT_ID:
            instance.agent = None
