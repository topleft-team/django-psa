from django.db import models
from model_utils import FieldTracker


class Action(models.Model):

    # start time
    action_arrival_date = models.DateTimeField(blank=True, null=True)

    # end time
    action_completion_date = models.DateTimeField(blank=True, null=True)

    action_date_created = models.DateTimeField(blank=True, null=True)
    time_taken = models.FloatField(blank=True, null=True)
    time_taken_adjusted = models.FloatField(blank=True, null=True)
    time_taken_days = models.FloatField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    action_charge_amount = models.FloatField(blank=True, null=True)
    action_charge_hours = models.FloatField(blank=True, null=True)
    action_non_charge_amount = models.FloatField(blank=True, null=True)
    action_non_charge_hours = models.FloatField(blank=True, null=True)
    act_is_billable = models.BooleanField(default=False)
    attachment_count = models.IntegerField(blank=True, null=True)
    charge_rate = models.IntegerField(blank=True, null=True)
    hidden_from_user = models.BooleanField(default=False)
    important = models.BooleanField(default=False)

    ticket = models.ForeignKey(
        'Ticket',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='ticket_actions'
    )
    project = models.ForeignKey(
        'Ticket',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='project_actions'
    )
    agent = models.ForeignKey(
        'Agent', blank=True, null=True, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Actions"

    def __str__(self):
        return f"Action {self.id}"

    API_FIELDS = {
        'id': 'id',
        'action_arrival_date': 'actionarrivaldate',
        'action_completion_date': 'actioncompletiondate',
        'time_taken': 'timetaken',
        'time_taken_adjusted': 'timetakenadjusted',
        'time_taken_days': 'timetakendays',
        'note': 'note',
        'action_charge_amount': 'actionchargeamount',
        'action_charge_hours': 'actionchargehours',
        'action_non_charge_amount': 'actionnonchargeamount',
        'action_non_charge_hours': 'actionnonchargehours',
        'act_is_billable': 'actisbillable',
        'attachment_count': 'attachment_count',
        'charge_rate': 'chargerate',
        'hidden_from_user': 'hiddenfromuser',
        'important': 'important',
        'ticket': 'ticket_id',
        'project': 'project_id',
        'agent': 'who_agentid',
    }


class ActionTracker(Action):
    tracker = FieldTracker()

    class Meta:
        proxy = True
        db_table = 'halo_action'
