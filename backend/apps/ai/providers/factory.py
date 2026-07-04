from django.conf import settings

from .mock_ai import MockAIProvider
from .mock_embeddings import MockEmbeddingProvider
from .ollama_ai import OllamaAIProvider
from .ollama_embeddings import OllamaEmbeddingProvider


def get_embedding_provider():
    if settings.EMBEDDING_PROVIDER == "ollama":
        return OllamaEmbeddingProvider(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.EMBEDDING_MODEL,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )
    return MockEmbeddingProvider(dimensions=settings.EMBEDDING_DIMENSIONS)


def get_ai_provider():
    if settings.AI_PROVIDER == "ollama":
        return OllamaAIProvider(base_url=settings.OLLAMA_BASE_URL, model=settings.AI_MODEL)
    return MockAIProvider(model=settings.AI_MODEL)
