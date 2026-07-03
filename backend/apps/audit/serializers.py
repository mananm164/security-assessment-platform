from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "client",
            "assessment",
            "actor",
            "action",
            "entity_type",
            "entity_id",
            "summary",
            "metadata",
            "created_at",
        )
        read_only_fields = fields
