from django.contrib import admin

from .models import Finding


@admin.register(Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = ("title", "assessment", "cvss_score", "severity", "status", "due_date", "created_by")
    list_filter = ("severity", "status")
    search_fields = ("title", "description", "cve_id", "assessment__name", "assessment__client__name")
