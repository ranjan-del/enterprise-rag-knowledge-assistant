"""Text chunking for the ingestion pipeline.

MEMORY.md checklist:
- [ ] Ingestion pipeline: parse -> chunk -> embed -> vector DB
"""

from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks.

    TODO: implement token-aware / sentence-aware chunking with overlap.
    """
    raise NotImplementedError
