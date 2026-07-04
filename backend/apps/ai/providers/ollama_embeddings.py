from __future__ import annotations

import json
from urllib.request import Request, urlopen


class OllamaEmbeddingProvider:
    provider_name = "ollama"

    def __init__(self, *, base_url: str, model: str, dimensions: int):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            payload = json.dumps({"model": self.model, "input": text}).encode("utf-8")
            request = Request(f"{self.base_url}/api/embed", data=payload, headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            embeddings = data.get("embeddings") or []
            vector = embeddings[0] if embeddings else data.get("embedding")
            if not isinstance(vector, list) or len(vector) != self.dimensions:
                raise ValueError("Embedding provider returned an unexpected vector length.")
            vectors.append([float(value) for value in vector])
        return vectors
