from rest_framework import serializers

from apps.findings.serializers import FindingSerializer
from .models import VulnerabilityIntel


class VulnerabilityIntelSerializer(serializers.ModelSerializer):
    class Meta:
        model = VulnerabilityIntel
        fields = (
            "cve_id",
            "nvd_description",
            "nvd_cvss_score",
            "nvd_cvss_vector",
            "cwe_ids",
            "references",
            "kev_listed",
            "kev_date_added",
            "epss_score",
            "epss_percentile",
            "source_retrieved_at",
            "last_refresh_attempt_at",
            "last_refresh_status",
            "last_safe_error",
        )


class FindingIntelligenceSerializer(serializers.Serializer):
    finding = FindingSerializer()
    intelligence = VulnerabilityIntelSerializer(allow_null=True)
    used_cache = serializers.BooleanField(default=False)
