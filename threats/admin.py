from django.contrib import admin

from .models import Threat


@admin.register(Threat)
class ThreatAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'source', 'created_at')
    list_filter = ('severity', 'created_at')
    search_fields = ('title', 'source', 'description')
