"""Vector store abstraction (Qdrant).

MEMORY.md checklist:
- [ ] Ingestion pipeline: parse -> chunk -> embed -> vector DB
- [ ] Retriever + search: semantic, metadata filter, hybrid
"""

from __future__ import annotations


class VectorStore:
    """Thin wrapper around the Qdrant client.

    TODO: initialise qdrant-client from settings and ensure the collection exists.
    """

    def upsert(self, ids: list[str], vectors: list[list[float]], payloads: list[dict]) -> None:
        # TODO: upsert embeddings + metadata payloads.
        raise NotImplementedError

    def search(self, vector: list[float], top_k: int = 5, filters: dict | None = None) -> list[dict]:
        # TODO: similarity search with optional metadata filter.
        raise NotImplementedError

    def delete(self, ids: list[str]) -> None:
        # TODO: delete vectors by id (e.g. when a document is removed).
        raise NotImplementedError
