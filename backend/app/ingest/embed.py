"""Embedding generation (offline-first).

The DEFAULT embedder is a deterministic bag-of-words hasher built on NumPy: each
token is hashed into one of ``dim`` buckets, counts are accumulated, and the
vector is L2-normalised. It needs no model download and no network, so retrieval
is fully reproducible and testable offline. Two texts sharing many words end up
with vectors pointing in a similar direction, so cosine similarity ranks
word overlap, which is enough to make retrieval meaningful.

A real ``sentence-transformers`` model can be dropped in later behind the same
interface; it is intentionally not required for the default path or the tests.
"""

from __future__ import annotations

import hashlib
import re

import numpy as np

from app.core.config import settings

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric word tokenizer (shared with lexical retrieval)."""
    return _TOKEN_RE.findall(text.lower())


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0  # avoid divide-by-zero for empty text
    return matrix / norms


class HashingEmbedder:
    """Deterministic bag-of-words embedder via the hashing trick (DEFAULT)."""

    def __init__(self, dim: int | None = None):
        self.dim = dim or settings.embedding_dim
        if self.dim <= 0:
            raise ValueError("dim must be positive")

    def _hash(self, token: str) -> int:
        # Use a stable hash (md5) rather than the salted built-in hash() so
        # embeddings are reproducible across processes and runs.
        digest = hashlib.md5(token.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "little") % self.dim

    def embed_one(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dim, dtype=np.float32)
        for token in tokenize(text):
            vector[self._hash(token)] += 1.0
        return _l2_normalize(vector.reshape(1, -1))[0]

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack([self.embed_one(t) for t in texts]).astype(np.float32)


# Process-wide default embedder (cheap to construct, but shared for clarity).
_default_embedder: HashingEmbedder | None = None


def get_embedder() -> HashingEmbedder:
    """Return the shared default (offline) embedder."""
    global _default_embedder
    if _default_embedder is None:
        _default_embedder = HashingEmbedder()
    return _default_embedder


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts and return plain lists of floats (JSON-serialisable)."""
    return [vec.tolist() for vec in get_embedder().embed(texts)]
