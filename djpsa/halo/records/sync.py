# This file is used to import all the synchronizers for the records module
# from a single location.

from django.utils.translation import gettext_lazy as _

from djpsa.halo.records.ticket.sync import TicketSynchronizer
from djpsa.halo.records.priority.sync import PrioritySynchronizer
from djpsa.halo.records.status.sync import StatusSynchronizer
from djpsa.halo.records.client.sync import ClientSynchronizer
from djpsa.halo.records.agent.sync import AgentSynchronizer
from djpsa.halo.records.site.sync import SiteSynchronizer
from djpsa.halo.records.sla.sync import SLASynchronizer
from djpsa.halo.records.appointment.sync import AppointmentSynchronizer
from djpsa.halo.records.halouser.sync import HaloUserSynchronizer
from djpsa.halo.records.tickettype.sync import TicketTypeSynchronizer
from djpsa.halo.records.action.sync import ActionSynchronizer
from djpsa.halo.records.team.sync import TeamSynchronizer
from djpsa.halo.records.budgettype.sync import BudgetTypeSynchronizer
from djpsa.halo.records.budgetdata.sync import BudgetDataSynchronizer
from djpsa.halo.records.outcome.sync import OutcomeSynchronizer
from djpsa.halo.records.chargerate.sync import ChargeRateSynchronizer
from djpsa.halo.records.timesheetevent.sync import TimeSheetEventSynchronizer
from djpsa.halo.records.fieldinfo.sync import FieldInfoSynchronizer
from djpsa.halo.records.cannedtext.sync import CannedTextSynchronizer

from djpsa.sync.grades import SyncGrades


class HaloSyncGrades(SyncGrades):
    def __init__(self, *args, **kwargs):
        super(HaloSyncGrades, self).__init__(*args, **kwargs)
        self.grades['partial'].synchronizers = [
            TicketSynchronizer,
        ]
        self.grades['operational'].synchronizers = [
            HaloUserSynchronizer,
            AgentSynchronizer,
            ClientSynchronizer,
            TicketSynchronizer,
            AppointmentSynchronizer,
            ActionSynchronizer,
        ]
        self.grades['configuration'].synchronizers = [
            SLASynchronizer,
            StatusSynchronizer,
            SiteSynchronizer,
            PrioritySynchronizer,
            TicketTypeSynchronizer,
            ChargeRateSynchronizer,
            OutcomeSynchronizer,
            TeamSynchronizer,
            BudgetTypeSynchronizer,
            BudgetDataSynchronizer,
            FieldInfoSynchronizer,
            CannedTextSynchronizer,
        ]


sync_command_list = [
        ('status', (StatusSynchronizer, _('Status'))),
        ('priority', (PrioritySynchronizer, _('Priority'))),
        ('client', (ClientSynchronizer, _('Client'))),
        ('sla', (SLASynchronizer, _('SLA'))),
        ('site', (SiteSynchronizer, _('Site'))),
        ('user', (HaloUserSynchronizer, _('User'))),
        ('agent', (AgentSynchronizer, _('Agent'))),
        ('chargerate', (ChargeRateSynchronizer, _('ChargeRate'))),
        ('outcome', (OutcomeSynchronizer, _('Outcome'))),
        ('ticket_type', (TicketTypeSynchronizer, _('TicketType'))),
        ('ticket', (TicketSynchronizer, _('Ticket'))),
        ('appointment', (AppointmentSynchronizer, _('Appointment'))),
        ('action', (ActionSynchronizer, _('Action'))),
        ('team', (TeamSynchronizer, _('Team'))),
        ('budget_type', (BudgetTypeSynchronizer, _('BudgetType'))),
        ('budget_data', (BudgetDataSynchronizer, _('BudgetData'))),
        ('field_info', (FieldInfoSynchronizer, _('FieldInfo'))),
        ('canned_text', (CannedTextSynchronizer, _('CannedText'))),
    ]
