"""Embedding generation for chunks.

MEMORY.md checklist:
- [ ] Ingestion pipeline: parse -> chunk -> embed -> vector DB
"""

from __future__ import annotations


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return an embedding vector per input text.

    TODO: load the configured sentence-transformers model and encode in batches.
    """
    raise NotImplementedError
