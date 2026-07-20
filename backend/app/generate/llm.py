"""Answer generation (offline-first).

Design goal for this repo: the pipeline must RUN OFFLINE with no API key. So the
DEFAULT backend is a deterministic *extractive* generator that stitches together
the top retrieved chunks with citation markers. It is not a learned model, but it
is fully reproducible and testable with zero external dependencies.

An optional Anthropic Claude backend can be enabled by setting ``ANTHROPIC_API_KEY``
in the environment; if the key is absent or the call fails for any reason, we fall
back to the extractive answer so the pipeline never hard-crashes. Secrets are read
from the environment only, never hardcoded.

MEMORY.md checklist:
- [x] Answer generation with confidence, citations, highlighted text, source document
"""

from __future__ import annotations

import os

# Model id kept as a constant so it is easy to find and change. Only used on the
# optional online path.
CLAUDE_MODEL = "claude-sonnet-4-5"


def build_prompt(question: str, context: str) -> str:
    """Build a grounded prompt instructing the model to answer only from context.

    The ``[n]`` markers in the context (added by the retriever) let the model cite
    its sources by number, which the citation layer maps back to chunk metadata.
    """
    return (
        "You are an internal knowledge assistant. Answer the question using ONLY "
        "the context below. Each passage is prefixed with a number like [1]. Cite "
        "the passages you use by their number, e.g. [1]. If the answer is not in "
        "the context, say you don't know.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )


def extractive_answer(question: str, chunks: list[dict], max_chunks: int = 3) -> str:
    """Deterministic offline answer: surface the top retrieved chunks.

    This is intentionally simple and reproducible. It is NOT a generated answer —
    it stitches the most relevant retrieved text together with ``[n]`` markers so
    the pipeline always produces a useful, grounded, testable response without an
    LLM.
    """
    if not chunks:
        return "I don't have enough information in the knowledge base to answer that."

    parts = []
    for i, chunk in enumerate(chunks[:max_chunks], start=1):
        snippet = " ".join(chunk.get("text", "").split())
        parts.append(f"[{i}] {snippet}")
    return "Based on the most relevant sources: " + " ".join(parts)


def generate(
    question: str,
    context: str,
    chunks: list[dict] | None = None,
    model: str | None = None,
) -> str:
    """Produce an answer for ``question`` grounded in ``context``.

    Tries Anthropic Claude when ``ANTHROPIC_API_KEY`` is set; otherwise (or on any
    failure) returns the deterministic extractive answer. The default path is
    fully offline.
    """
    chunks = chunks or []
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return extractive_answer(question, chunks)

    try:
        import anthropic

        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model or CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": build_prompt(question, context)}],
        )
        text = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        return text or extractive_answer(question, chunks)
    except Exception:
        # Any failure (missing SDK, network, auth) degrades gracefully offline.
        return extractive_answer(question, chunks)


class LLMClient:
    """Thin object-oriented wrapper around :func:`generate`.

    Kept for callers that prefer an injectable client. The default path is offline
    and requires no configuration.
    """

    def __init__(self, model: str | None = None):
        self.model = model

    def complete(self, question: str, context: str, chunks: list[dict] | None = None) -> str:
        return generate(question, context, chunks=chunks, model=self.model)
