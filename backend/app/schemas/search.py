"""Pydantic schemas for search + answers (stub).

MEMORY.md checklist:
- [ ] Answer generation with confidence, citations, highlighted text, source document
"""

from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    # TODO: top_k, filters, collection_id, mode (semantic|hybrid).


class Citation(BaseModel):
    # TODO: document_id, chunk_id, snippet, page.
    document_id: str


class AnswerResponse(BaseModel):
    answer: str
    # TODO: confidence: float, citations: list[Citation], highlights, source_document.
