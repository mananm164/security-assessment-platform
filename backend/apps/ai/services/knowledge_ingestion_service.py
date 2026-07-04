from __future__ import annotations

import hashlib
from pathlib import Path

from django.db import transaction
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from apps.ai.models import KnowledgeChunk, KnowledgeDocument
from apps.ai.providers.factory import get_embedding_provider
from .chunking import chunk_text


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise ValidationError("Knowledge document is missing YAML front matter.")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValidationError("Knowledge document front matter is not closed.")
    meta: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip('"')
    return meta, parts[2].strip()


class KnowledgeIngestionService:
    def __init__(self, *, embedding_provider=None):
        self.embedding_provider = embedding_provider or get_embedding_provider()

    @transaction.atomic
    def ingest_directory(self, directory: Path) -> dict:
        docs = sorted(directory.glob("*.md"))
        created_or_updated = 0
        chunks_written = 0
        for path in docs:
            result = self.ingest_file(path)
            created_or_updated += int(result["document_changed"])
            chunks_written += result["chunks_written"]
        return {"documents_seen": len(docs), "documents_changed": created_or_updated, "chunks_written": chunks_written}

    def ingest_file(self, path: Path) -> dict:
        text = path.read_text(encoding="utf-8")
        meta, body = parse_front_matter(text)
        required = {"title", "source_name", "source_url", "category"}
        if missing := required - set(meta):
            raise ValidationError(f"Knowledge document missing front matter keys: {', '.join(sorted(missing))}")
        content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        slug = slugify(path.stem)
        document, created = KnowledgeDocument.objects.get_or_create(
            slug=slug,
            defaults={
                "title": meta["title"],
                "source_name": meta["source_name"],
                "source_url": meta["source_url"],
                "category": meta["category"],
                "content_hash": content_hash,
                "is_active": True,
            },
        )
        document_changed = created or document.content_hash != content_hash or not document.is_active
        if not document_changed:
            return {"document_changed": False, "chunks_written": 0}
        document.title = meta["title"]
        document.source_name = meta["source_name"]
        document.source_url = meta["source_url"]
        document.category = meta["category"]
        document.content_hash = content_hash
        document.is_active = True
        document.save()
        document.chunks.all().delete()
        chunks = chunk_text(body)
        vectors = self.embedding_provider.embed(chunks)
        chunks_written = 0
        for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
            if len(vector) != 768:
                raise ValidationError("Embedding provider returned an unexpected vector length.")
            KnowledgeChunk.objects.create(
                document=document,
                chunk_index=index,
                content=chunk,
                content_hash=hashlib.sha256(chunk.encode("utf-8")).hexdigest(),
                embedding=vector,
                embedding_model=getattr(self.embedding_provider, "provider_name", "unknown"),
            )
            chunks_written += 1
        return {"document_changed": True, "chunks_written": chunks_written}
