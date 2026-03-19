from django.contrib import admin

from djpsa.platform.udf.models import UDFDefinition


@admin.register(UDFDefinition)
class UDFDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'display', 'record_type', 'udf_type', 'data_type', 'is_list')
    search_fields = ['name', 'display']
    list_filter = ('record_type', 'data_type', 'is_list')
