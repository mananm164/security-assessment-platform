from django.conf import settings
from django.db import models
from pgvector.django import VectorField


class KnowledgeDocument(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    source_name = models.CharField(max_length=255)
    source_url = models.URLField(max_length=500)
    category = models.CharField(max_length=80)
    content_hash = models.CharField(max_length=64)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class KnowledgeChunk(models.Model):
    document = models.ForeignKey(KnowledgeDocument, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    content_hash = models.CharField(max_length=64)
    embedding = VectorField(dimensions=768)
    embedding_model = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document", "chunk_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "chunk_index", "content_hash"], name="unique_knowledge_chunk_content"
            )
        ]

    def __str__(self) -> str:
        return f"{self.document.slug} #{self.chunk_index}"


class AIArtifact(models.Model):
    class ArtifactType(models.TextChoices):
        REMEDIATION = "REMEDIATION", "Remediation"

    finding = models.ForeignKey("findings.Finding", on_delete=models.CASCADE, related_name="ai_artifacts")
    artifact_type = models.CharField(max_length=30, choices=ArtifactType.choices, default=ArtifactType.REMEDIATION)
    provider = models.CharField(max_length=80)
    model = models.CharField(max_length=100)
    prompt_version = models.CharField(max_length=30, default="remediation-v1")
    content = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="ai_artifacts")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class AIArtifactSource(models.Model):
    artifact = models.ForeignKey(AIArtifact, on_delete=models.CASCADE, related_name="sources")
    knowledge_chunk = models.ForeignKey(KnowledgeChunk, on_delete=models.PROTECT, related_name="artifact_sources")
    rank = models.PositiveIntegerField()
    similarity = models.DecimalField(max_digits=6, decimal_places=5, null=True, blank=True)
    excerpt = models.CharField(max_length=500)

    class Meta:
        ordering = ["rank"]
        constraints = [
            models.UniqueConstraint(fields=["artifact", "knowledge_chunk"], name="unique_ai_artifact_source_chunk")
        ]
