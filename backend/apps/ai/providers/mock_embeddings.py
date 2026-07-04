from __future__ import annotations

import hashlib


class MockEmbeddingProvider:
    provider_name = "mock"

    def __init__(self, *, dimensions: int = 768):
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        lowered = text.lower()
        values = [0.0] * self.dimensions
        # Keyword buckets make tests deterministic and semantically useful.
        buckets = {
            0: ["access", "authorization", "idor", "bola", "permission"],
            1: ["header", "browser", "csp", "hsts"],
            2: ["patch", "dependency", "upgrade", "version"],
            3: ["validate", "validation", "retest", "evidence"],
            4: ["network", "exposure", "internet", "firewall", "tls"],
            5: ["log", "monitor", "alert", "detection"],
        }
        for index, keywords in buckets.items():
            values[index] = float(sum(lowered.count(keyword) for keyword in keywords))
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        for offset, byte in enumerate(digest):
            values[16 + offset] = byte / 255.0
        if not any(values):
            values[0] = 0.1
        return values
