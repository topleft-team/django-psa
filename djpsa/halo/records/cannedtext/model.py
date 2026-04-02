from django.db import models
from model_utils import FieldTracker


class CannedText(models.Model):
    name = models.CharField(max_length=255, blank=True, default='')
    text = models.TextField(blank=True, default='')
    team = models.ForeignKey(
        'Team',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    agent = models.ForeignKey(
        'Agent',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Canned text'
        verbose_name_plural = 'Canned texts'

    def __str__(self):
        return str(self.name) if self.name else f'CannedText {self.pk}'


class CannedTextTracker(CannedText):
    tracker = FieldTracker()

    class Meta:
        proxy = True
        db_table = 'halo_cannedtext'
