from django.contrib import admin

from djpsa.halo.records import models


@admin.register(models.Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'summary', 'client', 'status', 'priority', 'agent')
    search_fields = ['id', 'summary']


@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'inactive')
    search_fields = ['id', 'name']


@admin.register(models.Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'is_disabled')
    search_fields = ['id', 'name']


@admin.register(models.Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ['id', 'name']


@admin.register(models.Priority)
class PriorityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ['id', 'name']


@admin.register(models.TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ['id', 'name']


@admin.register(models.HaloUser)
class HaloUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'active')
    search_fields = ['id', 'name', 'email']


@admin.register(models.Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'start_date', 'end_date')
    search_fields = ['id', 'subject']


@admin.register(models.SLA)
class SLAAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ['id', 'name']


@admin.register(models.Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ['id', 'name']


@admin.register(models.Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'action_arrival_date',
        'action_completion_date',
        'time_taken',
        'note')
    search_fields = \
        ['id', 'ticket__id', 'time_taken', 'project__id', 'agent__id']
