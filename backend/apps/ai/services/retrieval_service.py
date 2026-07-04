from __future__ import annotations

from pgvector.django import CosineDistance

from apps.ai.models import KnowledgeChunk
from apps.ai.providers.factory import get_embedding_provider


class RetrievalService:
    def __init__(self, *, embedding_provider=None):
        self.embedding_provider = embedding_provider or get_embedding_provider()

    def retrieve(self, query: str, *, limit: int = 3):
        vector = self.embedding_provider.embed([query])[0]
        if len(vector) != 768:
            raise ValueError("Embedding provider returned an unexpected vector length.")
        return list(
            KnowledgeChunk.objects.filter(document__is_active=True)
            .select_related("document")
            .annotate(distance=CosineDistance("embedding", vector))
            .order_by("distance", "document__title", "chunk_index")[:limit]
        )
