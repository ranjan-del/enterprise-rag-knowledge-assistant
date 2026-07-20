"""Search + answer routes.

- ``POST /query`` runs retrieval (semantic or hybrid) then assembles a cited
  answer with confidence, citations, highlighted supporting text, and the source
  document, and logs the question for analytics.
- ``POST /semantic`` and ``POST /hybrid`` return raw ranked chunks for callers
  that want to build their own UI over the results.

MEMORY.md checklist:
- [x] Retriever + search: semantic, metadata filter, hybrid; organised into collections
- [x] Answer generation with confidence, citations, highlighted text, source document
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.generate.answer import build_answer
from app.models.document import QueryLog
from app.models.user import User
from app.retrieve.hybrid import HybridRetriever
from app.retrieve.retriever import Retriever
from app.schemas.search import AnswerResponse, SearchRequest, SearchResults

router = APIRouter()


def _retrieve(payload: SearchRequest) -> list[dict]:
    """Dispatch to the semantic or hybrid retriever based on the request mode."""
    if payload.mode == "hybrid":
        retriever = HybridRetriever()
    else:
        retriever = Retriever()
    return retriever.retrieve(
        payload.query,
        top_k=payload.top_k,
        collection_id=payload.collection_id,
        document_id=payload.document_id,
    )


@router.post("/query", response_model=AnswerResponse)
def query(
    payload: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnswerResponse:
    """Ask a question and get a cited, grounded answer."""
    retrieved = _retrieve(payload)
    result = build_answer(payload.query, retrieved)

    db.add(
        QueryLog(
            user_id=current_user.id,
            collection_id=payload.collection_id,
            question=payload.query,
            confidence=result["confidence"],
        )
    )
    db.commit()
    return AnswerResponse(**result)


@router.post("/semantic", response_model=SearchResults)
def semantic_search(
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
) -> SearchResults:
    """Return the most semantically similar chunks for a query."""
    payload.mode = "semantic"
    results = _retrieve(payload)
    return SearchResults(query=payload.query, mode="semantic", results=results)


@router.post("/hybrid", response_model=SearchResults)
def hybrid_search(
    payload: SearchRequest,
    current_user: User = Depends(get_current_user),
) -> SearchResults:
    """Return chunks ranked by a blend of lexical and semantic scores."""
    payload.mode = "hybrid"
    results = _retrieve(payload)
    return SearchResults(query=payload.query, mode="hybrid", results=results)
