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
            "triage_note",
            "triaged_by",
            "triaged_at",
            "duplicate_of",
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


class ObservationTriageSerializer(serializers.Serializer):
    triage_status = serializers.ChoiceField(
        choices=[
            ScannerObservation.TriageStatus.CONFIRMED,
            ScannerObservation.TriageStatus.FALSE_POSITIVE,
            ScannerObservation.TriageStatus.DUPLICATE,
        ]
    )
    triage_note = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    duplicate_of_id = serializers.IntegerField(required=False, allow_null=True)


class ObservationPromotionSerializer(serializers.Serializer):
    cvss_score = serializers.DecimalField(max_digits=3, decimal_places=1, min_value=0, max_value=10)
    business_impact = serializers.CharField(max_length=4000)
    remediation_owner = serializers.CharField(max_length=255)
    due_date = serializers.DateField()
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, max_length=4000)
    remediation = serializers.CharField(required=False, allow_blank=True, max_length=4000)
