from django.contrib import admin

from csw_services.models import CswService


@admin.register(CswService)
class CswServiceAdmin(admin.ModelAdmin):
    fields = ('service_type', 'uuid', 'title', 'abstract',  'owner', 'is_published')

    list_display = ('id', 'service_type', 'uuid', 'title', 'is_published')
    list_display_links = ('id', 'uuid')
    ordering = ('service_type', 'title',)