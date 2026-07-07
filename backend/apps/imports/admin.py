from django.contrib import admin

from .models import FindingSource, ImportPreview, ScanImport, ScanImportObservation, ScannerObservation


@admin.register(ScanImport)
class ScanImportAdmin(admin.ModelAdmin):
    list_display = ("id", "assessment", "source_tool", "status", "imported_by", "observations_created", "observations_updated", "created_at")
    list_filter = ("source_tool", "status")
    search_fields = ("source_filename", "file_sha256", "assessment__name")


@admin.register(ScannerObservation)
class ScannerObservationAdmin(admin.ModelAdmin):
    list_display = ("title", "assessment", "asset", "source_tool", "scanner_plugin_id", "triage_status", "last_seen_at")
    list_filter = ("source_tool", "triage_status", "scanner_plugin_id")
    search_fields = ("title", "external_id", "fingerprint", "raw_location")


@admin.register(ScanImportObservation)
class ScanImportObservationAdmin(admin.ModelAdmin):
    list_display = ("scan_import", "scanner_observation", "state", "observed_at")
    list_filter = ("state",)


@admin.register(FindingSource)
class FindingSourceAdmin(admin.ModelAdmin):
    list_display = ("finding", "scanner_observation", "first_seen_at", "last_seen_at")


@admin.register(ImportPreview)
class ImportPreviewAdmin(admin.ModelAdmin):
    list_display = ("id", "assessment", "source_tool", "source_filename", "observation_count", "created_by", "expires_at", "confirmed_at")
    list_filter = ("source_tool", "confirmed_at")
    search_fields = ("source_filename", "file_sha256", "assessment__name")
    readonly_fields = ("safe_observations",)
