from django.contrib import admin

from .models import NewsAlert, Threat


@admin.register(Threat)
class ThreatAdmin(admin.ModelAdmin):
    """Admin list/search options for manual threat records."""

    list_display = ('title', 'severity', 'source', 'created_at')
    list_filter = ('severity', 'created_at')
    search_fields = ('title', 'source', 'description')


@admin.register(NewsAlert)
class NewsAlertAdmin(admin.ModelAdmin):
    """Admin list/search options for news-generated alerts."""

    list_display = ('keyword', 'severity', 'source', 'created_at')
    list_filter = ('severity', 'source', 'created_at')
    search_fields = ('keyword', 'article_title', 'summary')
