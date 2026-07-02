from rest_framework import serializers

from .models import ScanImport, ScannerObservation


class ScanImportSerializer(serializers.ModelSerializer):
    imported_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ScanImport
        fields = (
            "id",
            "assessment",
            "source_tool",
            "source_filename",
            "file_sha256",
            "imported_by",
            "status",
            "created_at",
            "completed_at",
            "observations_created",
            "observations_updated",
            "error_summary",
        )
        read_only_fields = fields


class ScannerObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScannerObservation
        fields = (
            "id",
            "assessment",
            "asset",
            "source_tool",
            "external_id",
            "scanner_plugin_id",
            "fingerprint",
            "triage_status",
            "title",
            "description",
            "evidence_summary",
            "raw_severity",
            "confidence",
            "port",
            "protocol",
            "url",
            "suggested_remediation",
            "cve_ids",
            "cwe_ids",
            "references",
            "raw_location",
            "first_seen_at",
            "last_seen_at",
            "first_seen_import",
            "last_seen_import",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
