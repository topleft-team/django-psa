from django.db import models
from django_extensions.db.models import TimeStampedModel
from model_utils import FieldTracker


class UDFDefinition(TimeStampedModel):
    RECORD_TYPES = [
        ('ticket', 'Ticket'),
    ]

    record_type = models.CharField(max_length=50, choices=RECORD_TYPES)
    name = models.CharField(max_length=255)
    display = models.CharField(max_length=255)
    udf_type = models.CharField(max_length=50)
    data_type = models.CharField(max_length=50)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ('record_type', 'name')

    def __str__(self):
        return f"{self.display} ({self.record_type})"


class UDFDefinitionTracker(UDFDefinition):
    tracker = FieldTracker()

    class Meta:
        proxy = True
        db_table = 'sync_udfdefinition'
