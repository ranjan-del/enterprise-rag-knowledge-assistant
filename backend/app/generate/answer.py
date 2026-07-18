"""Answer assembly: confidence, citations, highlighted text, source document.

MEMORY.md checklist:
- [ ] Answer generation with confidence, citations, highlighted text, source document
"""

from __future__ import annotations


def build_answer(query: str, retrieved: list[dict]) -> dict:
    """Assemble the final answer payload returned to the UI.

    Returns (once implemented):
        answer: str          - generated answer text
        confidence: float    - TODO: confidence score
        citations: list      - TODO: citation references
        highlights: list     - TODO: highlighted supporting spans
        source_document: dict - TODO: primary source document metadata
    """
    # TODO: call LLMClient.complete, then attach confidence + citations + highlights.
    raise NotImplementedError
