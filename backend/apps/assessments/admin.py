from django.contrib import admin

from .models import Asset, Assessment


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "framework", "status", "start_date", "end_date", "created_by")
    list_filter = ("framework", "status")
    search_fields = ("name", "client__name", "scope_summary")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("display_name", "assessment", "asset_type", "environment", "criticality", "internet_exposed")
    list_filter = ("asset_type", "environment", "criticality", "internet_exposed")
    search_fields = ("display_name", "hostname", "ip_address", "base_url", "assessment__name")
