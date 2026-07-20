"""Hybrid retrieval: blend lexical overlap with semantic similarity.

Pure vector search can miss exact keyword matches (rare terms, product codes,
acronyms) whose meaning the hashing embedder smears across buckets. Pure keyword
search misses paraphrases. Hybrid search fuses both:

    fused = alpha * semantic + (1 - alpha) * lexical

Both component scores are min-max normalised to ``[0, 1]`` over the candidate set
before fusing, so neither scale dominates the other. ``alpha`` comes from
``settings.hybrid_alpha`` (default 0.6, i.e. slightly semantic-leaning).

The lexical score is the overlap coefficient between the query tokens and the
chunk tokens — simple, dependency-free, and reproducible, which keeps the whole
path offline and testable.

MEMORY.md checklist:
- [x] Retriever + search: hybrid
"""

from __future__ import annotations

import numpy as np

from app.core.config import settings
from app.ingest.embed import get_embedder, tokenize
from app.store.vector_store import get_store


def _minmax(values: np.ndarray) -> np.ndarray:
    """Scale an array to ``[0, 1]``; a flat array maps to all-zeros."""
    if values.size == 0:
        return values
    low = float(values.min())
    high = float(values.max())
    if high - low < 1e-12:
        return np.zeros_like(values)
    return (values - low) / (high - low)


def _lexical_score(query_tokens: set[str], text: str) -> float:
    """Overlap coefficient: fraction of query tokens present in the chunk."""
    if not query_tokens:
        return 0.0
    doc_tokens = set(tokenize(text))
    if not doc_tokens:
        return 0.0
    return len(query_tokens & doc_tokens) / len(query_tokens)


class HybridRetriever:
    """Blend keyword overlap and vector similarity, then re-rank."""

    def __init__(self, store=None, embedder=None, alpha: float | None = None):
        self.store = store or get_store()
        self.embedder = embedder or get_embedder()
        self.alpha = settings.hybrid_alpha if alpha is None else alpha

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        collection_id: int | None = None,
        document_id: int | None = None,
    ) -> list[dict]:
        """Return the ``top_k`` chunks ranked by the fused score."""
        meta = self.store.all_meta()
        if not meta:
            return []

        # Semantic scores for every stored chunk (cosine similarity).
        query_vector = self.embedder.embed_one(query)
        semantic = self.store.score_all(query_vector)

        # Restrict to the candidates that pass the metadata filters.
        candidates = [
            i
            for i in range(len(meta))
            if (collection_id is None or meta[i].get("collection_id") == collection_id)
            and (document_id is None or meta[i].get("document_id") == document_id)
        ]
        if not candidates:
            return []

        query_tokens = set(tokenize(query))
        semantic_c = np.array([semantic[i] for i in candidates], dtype=np.float32)
        lexical_c = np.array(
            [_lexical_score(query_tokens, meta[i]["text"]) for i in candidates],
            dtype=np.float32,
        )

        fused = self.alpha * _minmax(semantic_c) + (1 - self.alpha) * _minmax(lexical_c)

        order = np.argsort(-fused)[:top_k]
        results: list[dict] = []
        for rank in order:
            idx = candidates[int(rank)]
            record = dict(meta[idx])
            # Keep the raw cosine as ``score`` (used for confidence + display) and
            # expose the fused ranking score separately for transparency.
            record["score"] = float(semantic[idx])
            record["hybrid_score"] = float(fused[int(rank)])
            results.append(record)
        return results
