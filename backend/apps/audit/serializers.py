from rest_framework import serializers

from .models import AuditLog


class AuditActorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()


class AuditLogSerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()

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
            "safe_metadata",
            "created_at",
        )
        read_only_fields = fields

    def get_actor(self, obj):
        if obj.actor_id is None:
            return None
        return {"id": obj.actor_id, "email": obj.actor.email}
