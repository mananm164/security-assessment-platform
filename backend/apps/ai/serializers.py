from rest_framework import serializers

from apps.ai.models import AIArtifact, AIArtifactSource


class AIArtifactSourceSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="knowledge_chunk.document.title", read_only=True)
    source_name = serializers.CharField(source="knowledge_chunk.document.source_name", read_only=True)
    source_url = serializers.CharField(source="knowledge_chunk.document.source_url", read_only=True)
    category = serializers.CharField(source="knowledge_chunk.document.category", read_only=True)

    class Meta:
        model = AIArtifactSource
        fields = ("rank", "similarity", "excerpt", "title", "source_name", "source_url", "category")


class AIArtifactSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    sources = AIArtifactSourceSerializer(many=True, read_only=True)
    review_label = serializers.SerializerMethodField()

    class Meta:
        model = AIArtifact
        fields = (
            "id",
            "finding",
            "artifact_type",
            "provider",
            "model",
            "prompt_version",
            "content",
            "created_by",
            "created_at",
            "review_label",
            "sources",
        )
        read_only_fields = fields

    def get_review_label(self, obj):
        return "Draft — human review required"
