"""In-memory cosine-similarity vector store (offline-first, default backend).

Chunk vectors are kept in one ``(n, dim)`` NumPy matrix and ranked with a single
matrix-vector product; because the embedder L2-normalises every vector, that dot
product IS the cosine similarity. This needs no server, no network, and nothing
beyond NumPy, which keeps the whole pipeline runnable and testable offline.

Vectors are also persisted to the database (``chunks.embedding``), so this
in-memory index is rebuilt from the DB on startup via ``rebuild_from_db`` and
kept in sync on ingest/delete. A managed backend (e.g. Qdrant) could implement
the same ``upsert`` / ``search`` / ``delete_document`` surface later without
touching the retriever.

The module exposes a process-wide singleton via ``get_store`` because a single
FastAPI process shares one index across requests.
"""

from __future__ import annotations

import numpy as np

from app.core.config import settings


class InMemoryVectorStore:
    """Cosine-similarity store over an in-memory NumPy matrix."""

    def __init__(self, dim: int | None = None):
        self.dim = dim or settings.embedding_dim
        self._vectors: np.ndarray = np.zeros((0, self.dim), dtype=np.float32)
        # Parallel metadata list; index i describes row i of ``_vectors``.
        self._meta: list[dict] = []

    def upsert(self, records: list[dict]) -> None:
        """Add records. Each record needs ``vector`` plus citation metadata.

        Expected keys per record: ``vector`` (list/ndarray), ``chunk_id``,
        ``document_id``, ``collection_id``, ``filename``, ``page``,
        ``chunk_index``, ``text``.
        """
        if not records:
            return
        vectors = np.vstack(
            [np.asarray(r["vector"], dtype=np.float32) for r in records]
        )
        if vectors.shape[1] != self.dim:
            raise ValueError(
                f"vector dim {vectors.shape[1]} does not match store dim {self.dim}"
            )
        self._vectors = np.vstack([self._vectors, vectors])
        for record in records:
            self._meta.append({k: v for k, v in record.items() if k != "vector"})

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        collection_id: int | None = None,
        document_id: int | None = None,
    ) -> list[dict]:
        """Return the ``top_k`` most similar chunks, newest metadata included.

        Optional ``collection_id`` / ``document_id`` apply a metadata filter
        before ranking (semantic search scoped to a collection or document).
        """
        if len(self._meta) == 0:
            return []

        query = np.asarray(query_vector, dtype=np.float32).reshape(-1)
        scores = self._vectors @ query  # cosine similarity (vectors are unit-norm)

        # Build the candidate index set after applying metadata filters.
        candidates = range(len(self._meta))
        if collection_id is not None:
            candidates = [
                i for i in candidates if self._meta[i].get("collection_id") == collection_id
            ]
        if document_id is not None:
            candidates = [
                i for i in candidates if self._meta[i].get("document_id") == document_id
            ]
        candidates = list(candidates)
        if not candidates:
            return []

        candidates.sort(key=lambda i: scores[i], reverse=True)
        results: list[dict] = []
        for i in candidates[:top_k]:
            record = dict(self._meta[i])
            record["score"] = float(scores[i])
            results.append(record)
        return results

    def all_meta(self) -> list[dict]:
        """Return the parallel metadata list (read-only view for hybrid search)."""
        return self._meta

    def score_all(self, query_vector: np.ndarray) -> np.ndarray:
        """Cosine similarity of ``query_vector`` against every stored chunk.

        Returns a ``(n,)`` array aligned with :meth:`all_meta`. Used by hybrid
        search, which needs the full score distribution (not just the top-k) to
        fuse with lexical scores.
        """
        if len(self._meta) == 0:
            return np.zeros((0,), dtype=np.float32)
        query = np.asarray(query_vector, dtype=np.float32).reshape(-1)
        return self._vectors @ query

    def delete_document(self, document_id: int) -> None:
        """Drop every chunk belonging to a document (on document deletion)."""
        keep = [
            i
            for i, meta in enumerate(self._meta)
            if meta.get("document_id") != document_id
        ]
        self._vectors = (
            self._vectors[keep] if keep else np.zeros((0, self.dim), dtype=np.float32)
        )
        self._meta = [self._meta[i] for i in keep]

    def clear(self) -> None:
        self._vectors = np.zeros((0, self.dim), dtype=np.float32)
        self._meta = []

    def rebuild_from_db(self, db) -> None:
        """Reload the index from persisted chunk rows (called on startup)."""
        # Local import avoids a circular import at module load time.
        from app.models.document import Chunk, Document

        self.clear()
        rows = (
            db.query(Chunk, Document.filename)
            .join(Document, Chunk.document_id == Document.id)
            .all()
        )
        records = [
            {
                "vector": chunk.embedding,
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "collection_id": chunk.collection_id,
                "filename": filename,
                "page": chunk.page,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
            }
            for chunk, filename in rows
        ]
        self.upsert(records)

    def __len__(self) -> int:
        return len(self._meta)


_store: InMemoryVectorStore | None = None


def get_store() -> InMemoryVectorStore:
    """Return the process-wide vector store singleton."""
    global _store
    if _store is None:
        _store = InMemoryVectorStore()
    return _store
