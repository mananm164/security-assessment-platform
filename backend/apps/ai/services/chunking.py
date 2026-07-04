from __future__ import annotations


def chunk_text(text: str, *, min_size: int = 700, max_size: int = 1000, overlap: int = 120) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if len(cleaned) <= max_size:
        return [cleaned]
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + max_size, len(cleaned))
        if end < len(cleaned):
            boundary = cleaned.rfind(". ", start + min_size, end)
            if boundary != -1:
                end = boundary + 1
        chunks.append(cleaned[start:end].strip())
        if end >= len(cleaned):
            break
        start = max(end - overlap, 0)
    return chunks
