from decimal import Decimal

from rest_framework import serializers

from apps.assessments.models import Asset, Assessment

from .models import Finding


class FindingSerializer(serializers.ModelSerializer):
    assessment = serializers.PrimaryKeyRelatedField(queryset=Assessment.objects.all())
    affected_asset = serializers.PrimaryKeyRelatedField(
        queryset=Asset.objects.all(),
        allow_null=True,
        required=False,
    )
    severity = serializers.CharField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Finding
        fields = (
            "id",
            "assessment",
            "affected_asset",
            "title",
            "description",
            "cve_id",
            "cvss_score",
            "severity",
            "business_impact",
            "remediation",
            "remediation_owner",
            "status",
            "due_date",
            "priority_score",
            "priority_label",
            "priority_explanation",
            "priority_reason",
            "priority_computed_at",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "severity", "priority_score", "priority_label", "priority_explanation", "priority_reason", "priority_computed_at", "created_by", "created_at", "updated_at")

    def validate_cvss_score(self, value):
        if value < Decimal("0.0") or value > Decimal("10.0"):
            raise serializers.ValidationError("CVSS score must be between 0.0 and 10.0.")
        return value

    def validate(self, attrs):
        assessment = attrs.get("assessment", getattr(self.instance, "assessment", None))
        affected_asset = attrs.get("affected_asset", getattr(self.instance, "affected_asset", None))
        if affected_asset and assessment and affected_asset.assessment_id != assessment.id:
            raise serializers.ValidationError(
                {"affected_asset": "Affected asset must belong to the selected assessment."}
            )
        return attrs
