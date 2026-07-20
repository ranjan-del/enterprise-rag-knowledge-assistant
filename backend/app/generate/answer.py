"""Answer assembly: answer text, confidence, citations, highlights, source doc.

Takes the ranked chunks from a retriever and packages the full answer payload the
UI renders:

- ``answer``          — grounded answer text (offline extractive by default).
- ``confidence``      — the top chunk's cosine similarity, in ``[0, 1]``.
- ``citations``       — one entry per retrieved chunk (``[1]``, ``[2]`` ...) with
                        source filename, page, score and a snippet.
- ``highlights``      — query terms found in the top chunk, with character spans,
                        so the frontend can highlight the supporting text.
- ``source_document`` — the primary (top-ranked) source's metadata.

MEMORY.md checklist:
- [x] Answer generation with confidence, citations, highlighted text, source document
"""

from __future__ import annotations

from app.generate import llm
from app.ingest.embed import tokenize

_MAX_SNIPPET = 240


def _assemble_context(chunks: list[dict], budget: int = 4000) -> str:
    """Concatenate ranked chunks into a ``[n]``-marked context within a budget."""
    parts: list[str] = []
    used = 0
    for i, chunk in enumerate(chunks, start=1):
        block = f"[{i}] {chunk.get('text', '')}"
        if used + len(block) > budget and parts:
            break
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts)


def _build_citations(chunks: list[dict]) -> list[dict]:
    """Map each retrieved chunk back to its source metadata, in rank order."""
    citations: list[dict] = []
    for i, chunk in enumerate(chunks, start=1):
        text = chunk.get("text", "")
        snippet = text[:_MAX_SNIPPET].strip()
        if len(text) > _MAX_SNIPPET:
            snippet += "…"
        citations.append(
            {
                "marker": f"[{i}]",
                "chunk_id": chunk.get("chunk_id"),
                "document_id": chunk.get("document_id"),
                "filename": chunk.get("filename"),
                "page": chunk.get("page"),
                "score": round(float(chunk.get("score", 0.0)), 4),
                "snippet": snippet,
            }
        )
    return citations


def _build_highlights(query: str, top_chunk: dict) -> list[dict]:
    """Find query-term occurrences in the top chunk (character spans).

    Returns non-overlapping ``{term, start, end}`` spans so the UI can wrap the
    matching text. Purely lexical and deterministic — good enough to visibly show
    *why* a chunk was retrieved.
    """
    text = top_chunk.get("text", "")
    if not text:
        return []
    lowered = text.lower()
    terms = {t for t in tokenize(query) if len(t) >= 3}
    spans: list[dict] = []
    for term in terms:
        start = 0
        while True:
            idx = lowered.find(term, start)
            if idx == -1:
                break
            spans.append({"term": term, "start": idx, "end": idx + len(term)})
            start = idx + len(term)
    # Sort by position and drop overlaps so the frontend can splice cleanly.
    spans.sort(key=lambda s: (s["start"], -s["end"]))
    deduped: list[dict] = []
    last_end = -1
    for span in spans:
        if span["start"] >= last_end:
            deduped.append(span)
            last_end = span["end"]
    return deduped


def build_answer(query: str, retrieved: list[dict]) -> dict:
    """Assemble the final answer payload returned to the UI.

    Args:
        query: the user's question.
        retrieved: ranked chunks from a retriever (each with ``text``, ``score``
            and citation metadata).

    Returns:
        ``{question, answer, confidence, citations, highlights, source_document,
        retrieved}``.
    """
    if not retrieved:
        return {
            "question": query,
            "answer": llm.extractive_answer(query, []),
            "confidence": 0.0,
            "citations": [],
            "highlights": [],
            "source_document": None,
            "retrieved": [],
        }

    context = _assemble_context(retrieved)
    answer_text = llm.generate(query, context, chunks=retrieved)

    top = retrieved[0]
    # Cosine similarity of unit vectors with non-negative counts lands in [0, 1];
    # clamp defensively so confidence is always a clean probability-like number.
    confidence = round(max(0.0, min(1.0, float(top.get("score", 0.0)))), 4)

    source_document = {
        "document_id": top.get("document_id"),
        "filename": top.get("filename"),
        "page": top.get("page"),
        "collection_id": top.get("collection_id"),
    }

    return {
        "question": query,
        "answer": answer_text,
        "confidence": confidence,
        "citations": _build_citations(retrieved),
        "highlights": _build_highlights(query, top),
        "source_document": source_document,
        "retrieved": retrieved,
    }
