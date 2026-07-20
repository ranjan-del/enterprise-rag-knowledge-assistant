"""Analytics routes powering the dashboard tiles and usage view.

MEMORY.md checklist:
- [x] Dashboard: documents, users, search, analytics, collections
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.document import Chunk, Collection, Document, QueryLog
from app.models.user import User

router = APIRouter()


@router.get("/overview")
def overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Aggregate counts for the dashboard summary tiles."""
    return {
        "documents": db.query(Document).count(),
        "collections": db.query(Collection).count(),
        "chunks": db.query(Chunk).count(),
        "users": db.query(User).count(),
        "queries": db.query(QueryLog).count(),
        "ready_documents": db.query(Document)
        .filter(Document.status == "ready")
        .count(),
    }


@router.get("/usage")
def usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Recent questions and the most-referenced documents."""
    recent = (
        db.query(QueryLog).order_by(QueryLog.created_at.desc()).limit(10).all()
    )
    recent_queries = [
        {
            "question": log.question,
            "confidence": round(float(log.confidence), 4),
            "created_at": log.created_at.isoformat(),
        }
        for log in recent
    ]

    top_docs = (
        db.query(Document.id, Document.filename, func.count(Chunk.id).label("chunks"))
        .join(Chunk, Chunk.document_id == Document.id)
        .group_by(Document.id, Document.filename)
        .order_by(func.count(Chunk.id).desc())
        .limit(5)
        .all()
    )
    top_documents = [
        {"document_id": doc_id, "filename": filename, "chunks": chunks}
        for doc_id, filename, chunks in top_docs
    ]

    return {"recent_queries": recent_queries, "top_documents": top_documents}
