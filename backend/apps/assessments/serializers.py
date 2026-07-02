from rest_framework import serializers

from apps.tenancy.models import Client

from .models import Asset, Assessment


class AssessmentSerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all())
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Assessment
        fields = (
            "id",
            "client",
            "name",
            "framework",
            "status",
            "start_date",
            "end_date",
            "scope_summary",
            "created_by",
            "created_at",
        )
        read_only_fields = ("id", "created_by", "created_at")

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date cannot be before start date."})
        return attrs


class AssetSerializer(serializers.ModelSerializer):
    assessment = serializers.PrimaryKeyRelatedField(queryset=Assessment.objects.all())

    class Meta:
        model = Asset
        fields = (
            "id",
            "assessment",
            "asset_type",
            "display_name",
            "hostname",
            "ip_address",
            "base_url",
            "environment",
            "criticality",
            "internet_exposed",
            "owner",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        values = {
            "display_name": attrs.get("display_name", getattr(self.instance, "display_name", "")),
            "hostname": attrs.get("hostname", getattr(self.instance, "hostname", "")),
            "ip_address": attrs.get("ip_address", getattr(self.instance, "ip_address", None)),
            "base_url": attrs.get("base_url", getattr(self.instance, "base_url", "")),
        }
        if not any(values.values()):
            raise serializers.ValidationError(
                "Asset must have at least one identifier: display name, hostname, IP address or base URL."
            )
        return attrs
