from djpsa.halo import models
from djpsa.halo.records import api
from djpsa.halo import sync
from djpsa.halo.records.halouser.model import HaloUser


class ActionSynchronizer(sync.ResponseKeyMixin,
                         sync.HaloChildFetchRecordsMixin,
                         sync.CreateMixin,
                         sync.UpdateMixin,
                         sync.HaloSynchronizer,
                         ):
    lookup_key = 'ticket_action_id'
    model_class = models.ActionTracker
    client_class = api.ActionAPI
    response_key = 'actions'
    parent_field = 'ticket_id'
    parent_model_class = models.Ticket

    related_meta = {
        'ticket_id': (models.TicketTracker, 'ticket'),
        'project_id': (models.TicketTracker, 'project'),
        'who_agentid': (models.Agent, 'agent'),
        'outcome_id': (models.Outcome, 'outcome'),
        'charge_rate_id': (models.ChargeRate, 'chargerate'),
    }

    def _get_real_action_id(self, action_record):
        """
        Extract the real action ID from the concatenated ID.
        The Action model stores concatenated IDs
        (ticket_id + action_id) as the primary key
        """
        concatenated_id = str(action_record.id)
        ticket_id = str(
            action_record.ticket.id if action_record.ticket
            else action_record.project.id
        )

        if concatenated_id.startswith(ticket_id):
            real_action_id = concatenated_id[len(ticket_id):]
            return int(real_action_id)

        return action_record.id

    def update(self, record, data, *args, **kwargs):
        """
        Override update to use the real action ID
        instead of the concatenated ID.
        """
        real_action_id = self._get_real_action_id(record)

        data = self._convert_fields(data)
        body = self._convert_fields_to_api_format(data)

        body.update({'id': real_action_id})
        response = self.client.update(real_action_id, body)

        instance, _ = self.update_or_create_instance(response)
        return instance

    def update_or_create_instance(self, json_data):
        # So far, action is the only model that has to be treated in this way,
        #  so rather than updating the lookup_key pattern to be more generic,
        #  we'll just add this special case here. As I think it would just add
        #  confusion if there is such a generic pattern for one model, and
        #  EVERYTHING else.

        # Action IDs are only unique per ticket, so concatenate the ticket ID
        # with the action ID
        json_data[self.lookup_key] = \
            int(f"{json_data.get('ticket_id')}{json_data.get('id')}")

        return super().update_or_create_instance(json_data)

    def _assign_field_data(self, instance, json_data):
        instance.id = json_data.get(self.lookup_key)
        instance.action_arrival_date = \
            sync.empty_date_parser(json_data.get('actionarrivaldate'))
        instance.action_completion_date = \
            sync.empty_date_parser(json_data.get('actioncompletiondate'))
        instance.action_date_created = \
            sync.empty_date_parser(json_data.get('actiondatecreated'))
        instance.time_taken = json_data.get('timetaken')
        instance.time_taken_adjusted = json_data.get('timetakenadjusted')
        instance.time_taken_days = json_data.get('timetakendays')
        instance.non_billable_time = json_data.get('nonbilltime')
        instance.travel_time = json_data.get('traveltime')
        instance.note = json_data.get('note')
        instance.action_charge_amount = json_data.get('actionchargeamount')
        instance.action_charge_hours = json_data.get('actionchargehours')
        instance.action_non_charge_amount = \
            json_data.get('actionnonchargeamount')
        instance.action_non_charge_hours = \
            json_data.get('actionnonchargehours')
        instance.attachment_count = json_data.get('attachment_count')
        instance.act_is_billable = json_data.get('actisbillable', False)
        instance.hidden_from_user = json_data.get('hiddenfromuser', False)
        instance.important = json_data.get('important', False)

        self.set_relations(instance, json_data)

    def create(self, data, *args, **kwargs):
        # Halo impersonation is a bit weird, we need to get the agent's
        # username from the user record related to the agent. Also, the
        # username field is called "name".
        data['agent'] = HaloUser.objects.get(agent=data['agent']).name

        return super().create(data, *args, **kwargs)
