from django.utils import timezone
from dateutil.parser import parse

from djpsa.halo import models
from djpsa.halo import api

from djpsa.sync.sync import Synchronizer


# README #
#
# "response_key"
#    The Halo API is very inconsistent, the response_key field is used to
#     specify the key in the response that contains the data we want to unpack.
#
#     Where when the response is just a list with no key, the response_key is
#     omitted from the class. ResponseKeyMixin should be applied to any class
#     that requires the response_key field.
#
# "lookup_key"
#    Some records need to be tracked by a different field than id for the
#     primary key. For example, the priority model uses priorityid as the
#     primary key, so the lookup_key is set to 'priorityid'. This is because
#     in the Halo API the 'id' seems to be a large alphanumeric string, and
#     isn't used on the ticket model.


def empty_date_parser(date_time):
    # Halo API returns a date of 1/1/1900 or earlier as an empty date.
    # This will set the model fields as None if it is an impossible date.
    # Set to 1980 in case they also do 1950 or something and I haven't seen it.
    if date_time:
        date_time = timezone.make_aware(parse(date_time), timezone.utc)
        return date_time if date_time.year > 1980 else None


class ResponseKeyMixin:
    response_key = None

    def _unpack_records(self, response):
        records = response[self.response_key]
        return records


class TicketSynchronizer(ResponseKeyMixin, Synchronizer):
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

    def __init__(self, full=False, *args, **kwargs):

        if full:
            self.conditions.append({
                'open_only': True,
            })

        super().__init__(full, *args, **kwargs)

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
            instance.start_time = parse(json_data.get('starttime'))

        target_date = json_data.get('targetdate')
        instance.target_date = empty_date_parser(target_date)

        if instance.target_date:
            instance.target_time = parse(json_data.get('targettime'))

        last_incoming_email_date = json_data.get('lastincomingemaildate')
        instance.last_incoming_email_date = empty_date_parser(last_incoming_email_date)

        self.set_relations(instance, json_data)


class StatusSynchronizer(Synchronizer):
    model_class = models.StatusTracker
    client_class = api.StatusAPI

    def _assign_field_data(self, instance, json_data):

        instance.id = json_data.get('id')
        instance.name = json_data.get('name')
        instance.colour = json_data.get('colour')


class PrioritySynchronizer(Synchronizer):
    model_class = models.PriorityTracker
    lookup_key = 'priorityid'
    client_class = api.PriorityAPI

    def _assign_field_data(self, instance, json_data):

        instance.id = json_data.get('priorityid')
        instance.name = json_data.get('name')
        instance.colour = json_data.get('colour')
        instance.is_hidden = json_data.get('ishidden')


class ClientSynchronizer(ResponseKeyMixin, Synchronizer):
    response_key = 'clients'
    model_class = models.ClientTracker
    client_class = api.ClientAPI

    related_meta = {
        'main_site_id': (models.Site, 'site'),
    }

    def __init__(self, full=False, *args, **kwargs):

        self.conditions.append({
            'includeactive': True,
        })

        super().__init__(full, *args, **kwargs)

    def _assign_field_data(self, instance, json_data):

        instance.id = json_data.get('id')
        instance.name = json_data.get('name')
        instance.inactive = json_data.get('inactive')
        instance.phone_number = json_data.get('main_phonenumber')

        self.set_relations(instance, json_data)


class AgentSynchronizer(Synchronizer):
    model_class = models.AgentTracker
    client_class = api.AgentAPI

    def __init__(self, full=False, *args, **kwargs):

        self.conditions.append({
            'includeactive': True,
        })

        super().__init__(full, *args, **kwargs)

    def _assign_field_data(self, instance, json_data):

        instance.id = json_data.get('id')
        instance.name = json_data.get('name')
        instance.is_disabled = json_data.get('isdisabled')
        instance.email = json_data.get('email')
        instance.initials = json_data.get('initials')
        instance.firstname = json_data.get('firstname')
        instance.surname = json_data.get('surname')
        instance.colour = json_data.get('colour')


class SLASynchronizer(Synchronizer):
    model_class = models.SLATracker
    client_class = api.StatusAPI

    def _assign_field_data(self, instance, json_data):

        instance.id = json_data.get('id')
        instance.name = json_data.get('name')
        instance.hours_are_techs_local_time = json_data.get('hoursaretechslocaltime', False)
        instance.response_reset = json_data.get('responsereset', False)
        instance.response_reset_approval = json_data.get('response_reset_approval', False)
        instance.track_sla_fix_by_time = json_data.get('trackslafixbytime', False)
        instance.track_sla_response_time = json_data.get('trackslaresponsetime', False)
        instance.workday_id = json_data.get('workday_id')
        instance.auto_release_limit = json_data.get('autoreleaselimit')
        instance.auto_release_option = json_data.get('autoreleaseoption', False)
        instance.status_after_first_warning = json_data.get('statusafterfirstwarning')
        instance.status_after_second_warning = json_data.get('statusaftersecondwarning')
        instance.status_after_auto_release = json_data.get('statusafterautorelease')


class SiteSynchronizer(ResponseKeyMixin, Synchronizer):
    model_class = models.SiteTracker
    response_key = 'sites'
    client_class = api.SiteAPI

    related_meta = {
        'client_id': (models.Client, 'client'),
        'sla_id': (models.SLA, 'sla'),
    }

    def __init__(self, full=False, *args, **kwargs):

        self.conditions.append({
            'includeaddress': True,
        })

        super().__init__(full, *args, **kwargs)

    def _assign_field_data(self, instance, json_data):

        instance.id = json_data.get('id')
        instance.name = json_data.get('name')
        # api has client_id as decimal, convert to int. It's never
        # actually a decimal. The API docs has it as an int, but for some
        # reason it's being returned as a decimal on Site records.
        if json_data.get('client_id'):
            json_data['client_id'] = int(json_data.get('client_id'))

        # This is the worst thing I have ever seen.
        instance.delivery_address = json_data.get('delivery_address_line1')
        instance.delivery_address += " {}".format(json_data.get('delivery_address_line2'))
        instance.delivery_address += " {}".format(json_data.get('delivery_address_line3'))
        instance.delivery_address += " {}".format(json_data.get('delivery_address_line4'))
        instance.delivery_address += " {}".format(json_data.get('delivery_address_line5'))

        instance.colour = json_data.get('colour')
        instance.active = json_data.get('active', False)
        instance.phone_number = json_data.get('phone_number')
        instance.use = json_data.get('use')

        self.set_relations(instance, json_data)


class HaloUserSynchronizer(ResponseKeyMixin, Synchronizer):
    model_class = models.HaloUserTracker
    response_key = 'users'
    client_class = api.UserAPI

    related_meta = {
        'client_id': (models.Client, 'client'),
        'linked_agent_id': (models.Agent, 'agent'),
    }

    def __init__(self, full=False, *args, **kwargs):

        self.conditions.append({
            'includeactive': True,
        })

        super().__init__(full, *args, **kwargs)

    def _assign_field_data(self, instance, json_data):
        instance.id = json_data.get('id')
        instance.name = json_data.get('name')
        instance.first_name = json_data.get('firstname')
        instance.surname = json_data.get('surname')
        instance.initials = json_data.get('initials')
        instance.email = json_data.get('emailaddress')
        instance.colour = json_data.get('colour')
        instance.active = not json_data.get('inactive', True)
        instance.login = json_data.get('login')
        instance.use = json_data.get('use')
        instance.never_send_emails = json_data.get('neversendemails', False)
        instance.phone_number = json_data.get('phonenumber')
        instance.mobile_number = json_data.get('mobilenumber')
        instance.mobile_number_2 = json_data.get('mobilenumber2')
        instance.home_number = json_data.get('homenumber')
        instance.tel_pref = json_data.get('telpref')
        instance.is_service_account = json_data.get('isserviceaccount', False)
        instance.is_important_contact = json_data.get('isimportantcontact', False)
        instance.is_important_contact_2 = json_data.get('isimportantcontact2', False)

        if json_data.get('linked_agent_id') == 0:
            json_data['linked_agent_id'] = None

        self.set_relations(instance, json_data)


class AppointmentSynchronizer(Synchronizer):
    model_class = models.AppointmentTracker
    client_class = api.AppointmentAPI

    related_meta = {
        'client_id': (models.Client, 'client'),
        'agent_id': (models.Agent, 'agent'),
        'site_id': (models.Site, 'site'),
        'user_id': (models.HaloUser, 'user'),
        'ticket_id': (models.Ticket, 'ticket'),
    }

    def __init__(self, full=False, *args, **kwargs):

        self.conditions.append({
            'hidecompleted': True,
        })

        super().__init__(full, *args, **kwargs)

    def _assign_field_data(self, instance, json_data):
        instance.id = json_data.get('id')
        instance.subject = json_data.get('subject')
        instance.start_date = timezone.make_aware(parse(json_data.get('start_date')), timezone.utc)
        instance.end_date = timezone.make_aware(parse(json_data.get('end_date')), timezone.utc)
        instance.appointment_type = json_data.get('appointment_type_name')
        instance.is_private = json_data.get('is_private')
        instance.is_task = json_data.get('is_task', False)
        instance.complete_status = json_data.get('complete_status')
        instance.colour = json_data.get('colour')
        instance.online_meeting_url = json_data.get('online_meeting_url')

        self.set_relations(instance, json_data)


class TicketTypeSyncronizer(Synchronizer):
    model_class = models.TicketTypeTracker
    client_class = api.TicketTypeAPI

    def _assign_field_data(self, instance, json_data):
        instance.id = json_data.get('id')
        instance.name = json_data.get('name')
        instance.description = json_data.get('description')
        instance.active = json_data.get('active', False)
        instance.use = json_data.get('use')
        instance.colour = json_data.get('colour')
