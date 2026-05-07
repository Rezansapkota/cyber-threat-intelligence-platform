from django.contrib import admin

from .models import NewsAlert, Threat


@admin.register(Threat)
class ThreatAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'source', 'created_at')
    list_filter = ('severity', 'created_at')
    search_fields = ('title', 'source', 'description')


@admin.register(NewsAlert)
class NewsAlertAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'severity', 'source', 'created_at')
    list_filter = ('severity', 'source', 'created_at')
    search_fields = ('keyword', 'article_title', 'summary')
