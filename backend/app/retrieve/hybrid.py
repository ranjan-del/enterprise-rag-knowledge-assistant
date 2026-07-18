"""Hybrid retrieval: combine lexical + semantic scores.

MEMORY.md checklist:
- [ ] Retriever + search: ... hybrid
"""

from __future__ import annotations


class HybridRetriever:
    """Blend keyword (BM25 / full-text) and vector similarity results."""

    def retrieve(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[dict]:
        # TODO: run lexical + semantic retrieval, fuse scores (e.g. RRF), re-rank.
        raise NotImplementedError
