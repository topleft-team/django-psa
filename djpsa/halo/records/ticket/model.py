from django.db import models
from model_utils import FieldTracker


class Ticket(models.Model):
    summary = models.CharField(blank=True, null=True, max_length=255)
    details = models.TextField(
        blank=True, null=True
    )
    status = models.ForeignKey('Status', on_delete=models.CASCADE)
    priority = models.ForeignKey(
        'Priority', blank=True, null=True, on_delete=models.CASCADE)
    client = models.ForeignKey(
        'Client', blank=True, null=True, on_delete=models.CASCADE)
    agent = models.ForeignKey(
        'Agent', blank=True, null=True, on_delete=models.CASCADE)
    sla = models.ForeignKey(
        'SLA', blank=True, null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(
        'HaloUser', blank=True, null=True, on_delete=models.CASCADE)
    site = models.ForeignKey(
        'Site', blank=True, null=True, on_delete=models.CASCADE)
    type = models.ForeignKey(
        'TicketType', blank=True, null=True, on_delete=models.CASCADE)
    project = models.ForeignKey(
        'Ticket', blank=True, null=True, on_delete=models.CASCADE)
    user_email = models.EmailField(blank=True, null=True)
    reported_by = models.CharField(max_length=255, blank=True, null=True)
    end_user_status = models.IntegerField(blank=True, null=True)
    category_1 = models.CharField(max_length=255, blank=True, null=True)
    category_2 = models.CharField(max_length=255, blank=True, null=True)
    category_3 = models.CharField(max_length=255, blank=True, null=True)
    category_4 = models.CharField(max_length=255, blank=True, null=True)
    inactive = models.BooleanField(default=False)
    sla_response_state = \
        models.CharField(max_length=255, blank=True, null=True)
    sla_hold_time = models.FloatField(blank=True, null=True)
    date_occurred = models.DateTimeField(blank=True, null=True)
    respond_by_date = models.DateTimeField(blank=True, null=True)
    fix_by_date = models.DateTimeField(blank=True, null=True)
    date_assigned = models.DateTimeField(blank=True, null=True)
    response_date = models.DateTimeField(blank=True, null=True)
    deadline_date = models.DateTimeField(blank=True, null=True)
    last_action_date = models.DateField(blank=True, null=True)
    last_update = models.DateTimeField(blank=True, null=True)

    # Target and Start date are actually 2 fields from Halo,
    # but we are syncing both into the same field in the model.
    target_date = models.DateField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)

    last_incoming_email = models.DateTimeField(blank=True, null=True)
    impact = models.IntegerField(blank=True, null=True)
    impact_level = models.IntegerField(blank=True, null=True)
    flagged = models.BooleanField(default=False)
    on_hold = models.BooleanField(default=False)
    project_time_actual = models.FloatField(blank=True, null=True)
    project_money_actual = models.FloatField(blank=True, null=True)
    cost = models.FloatField(blank=True, null=True)
    estimate = models.FloatField(blank=True, null=True)
    estimated_days = models.FloatField(blank=True, null=True)
    exclude_from_sla = models.BooleanField(default=False)
    team = models.CharField(max_length=255, blank=True, null=True)
    reviewed = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    email_to_list = models.TextField(blank=True, null=True)
    urgency = models.IntegerField(blank=True, null=True)
    service_status_note = \
        models.TextField(blank=True, null=True)
    ticket_tags = models.TextField(blank=True, null=True)
    appointment_type = models.CharField(max_length=255, blank=True, null=True)

    use = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Tickets"

    def __str__(self):
        return f"Ticket {self.id} - {self.summary}"


class TicketTracker(Ticket):
    tracker = FieldTracker()

    class Meta:
        proxy = True
        db_table = 'halo_ticket'
