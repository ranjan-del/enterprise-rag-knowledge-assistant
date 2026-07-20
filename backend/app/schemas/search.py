"""Pydantic schemas for search and cited answers.

MEMORY.md checklist:
- [x] Answer generation with confidence, citations, highlighted text, source document
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    collection_id: int | None = None
    document_id: int | None = None
    mode: str = Field(default="semantic", pattern="^(semantic|hybrid)$")


class SearchResultItem(BaseModel):
    chunk_id: int | None = None
    document_id: int | None = None
    filename: str | None = None
    page: int | None = None
    chunk_index: int | None = None
    score: float
    text: str


class SearchResults(BaseModel):
    query: str
    mode: str
    results: list[SearchResultItem]


class Citation(BaseModel):
    marker: str
    chunk_id: int | None = None
    document_id: int | None = None
    filename: str | None = None
    page: int | None = None
    score: float
    snippet: str


class Highlight(BaseModel):
    term: str
    start: int
    end: int


class SourceDocument(BaseModel):
    document_id: int | None = None
    filename: str | None = None
    page: int | None = None
    collection_id: int | None = None


class AnswerResponse(BaseModel):
    question: str
    answer: str
    confidence: float
    citations: list[Citation]
    highlights: list[Highlight]
    source_document: SourceDocument | None = None
