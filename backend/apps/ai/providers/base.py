from __future__ import annotations

from typing import Protocol


class AIProvider(Protocol):
    provider_name: str

    def generate_remediation(self, *, finding_context: dict, sources: list[dict]) -> str:
        ...


class EmbeddingProvider(Protocol):
    provider_name: str
    dimensions: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        ...
