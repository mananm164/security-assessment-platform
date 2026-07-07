from rest_framework import serializers

from .models import ImportPreview, ScanImport, ScannerObservation


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


class ImportPreviewSerializer(serializers.ModelSerializer):
    summary = serializers.SerializerMethodField()
    observations = serializers.SerializerMethodField()
    created_by = serializers.StringRelatedField(read_only=True)
    confirmed_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ImportPreview
        fields = (
            "id",
            "assessment",
            "source_tool",
            "source_filename",
            "file_sha256",
            "file_size_bytes",
            "parser_version",
            "observation_count",
            "created_by",
            "created_at",
            "expires_at",
            "confirmed_at",
            "confirmed_by",
            "scan_import",
            "summary",
            "observations",
        )
        read_only_fields = fields

    def get_summary(self, obj):
        from .services.preview_service import preview_summary

        return preview_summary(obj)

    def get_observations(self, obj):
        from .services.preview_service import preview_observation_sample

        return preview_observation_sample(obj)


class ImportPreviewConfirmSerializer(serializers.Serializer):
    scan_import_id = serializers.IntegerField()
    assessment = serializers.IntegerField()
    source_tool = serializers.CharField()
    observations_created = serializers.IntegerField()
    observations_reobserved = serializers.IntegerField()
    detail_url = serializers.CharField()


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
