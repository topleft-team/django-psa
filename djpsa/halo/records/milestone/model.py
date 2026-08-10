from django.db import models
from model_utils import FieldTracker


class Milestone(models.Model):
    """
    A milestone on a Halo project.

    Halo groups a project's tasks into ordered milestones, and a milestone can
    depend on another one (its tasks stay locked until the dependency is met).
    Halo exposes no completion flag or actual-end date, so "done" is derived
    from whether the milestone's member tickets are all closed.
    """
    # The project this milestone belongs to. In Halo a project is a Ticket.
    ticket = models.ForeignKey(
        'Ticket', on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=255, blank=True, null=True)
    sequence = models.IntegerField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    target_date = models.DateField(blank=True, null=True)
    # Halo's lock state: 0 not started, 1 locked by an unmet dependency,
    # 2 active. NOT completion — a milestone whose tickets are all closed
    # still reads 2.
    state = models.IntegerField(blank=True, null=True)

    class Meta:
        ordering = ['sequence', 'id']

    def __str__(self):
        return str(self.name)


class MilestoneTracker(Milestone):
    tracker = FieldTracker()

    class Meta:
        proxy = True
        db_table = 'halo_milestone'


class MilestoneDependency(models.Model):
    """
    A milestone-to-milestone dependency: ``child`` waits on ``parent``.

    This is the only dependency Halo models — there is no task-to-task
    predecessor field anywhere in its API.
    """
    child = models.ForeignKey(
        'Milestone', on_delete=models.CASCADE, related_name='dependencies')
    parent = models.ForeignKey(
        'Milestone', on_delete=models.CASCADE, related_name='dependents')

    class Meta:
        verbose_name_plural = "Milestone Dependencies"
        unique_together = [['child', 'parent']]

    def __str__(self):
        return '{} depends on {}'.format(self.child, self.parent)


class MilestoneDependencyTracker(MilestoneDependency):
    tracker = FieldTracker()

    class Meta:
        proxy = True
        db_table = 'halo_milestonedependency'
