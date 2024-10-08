from django.db import models
from model_utils import FieldTracker


class Agent(models.Model):
    name = models.CharField(max_length=255)
    is_disabled = models.BooleanField(default=False)
    email = models.EmailField(blank=True, null=True)
    initials = models.CharField(max_length=10, blank=True, null=True)
    firstname = models.CharField(max_length=255, blank=True, null=True)
    surname = models.CharField(max_length=255, blank=True, null=True)
    colour = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Agents"

    def __str__(self):
        return f"Agent {self.id} - {self.name}"


class AgentTracker(Agent):
    tracker = FieldTracker()

    class Meta:
        proxy = True
        db_table = 'halo_agent'
