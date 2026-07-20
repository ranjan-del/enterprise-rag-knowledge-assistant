"""Document upload + management routes.

Uploading a file runs the full ingestion pipeline (parse -> chunk -> embed ->
persist -> index) synchronously and returns the created document with its
ingestion status and chunk count. Deleting a document removes its rows and its
vectors from the in-memory index.

MEMORY.md checklist:
- [x] Multi-format upload + parsers (PDF, DOCX, PPTX, TXT, CSV)
- [x] Ingestion pipeline: parse -> chunk -> embed -> vector DB
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.ingest.parser import SUPPORTED_FORMATS
from app.ingest.pipeline import ingest_document
from app.models.document import Collection, Document
from app.models.user import Role, User
from app.schemas.document import DocumentList, DocumentOut
from app.store.vector_store import get_store

router = APIRouter()


@router.get("", response_model=DocumentList)
def list_documents(
    collection_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentList:
    """List documents, optionally filtered to a single collection."""
    query = db.query(Document)
    if collection_id is not None:
        query = query.filter(Document.collection_id == collection_id)
    items = query.order_by(Document.created_at.desc()).all()
    return DocumentList(items=items, total=len(items))


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    collection_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    """Upload a file and ingest it into the knowledge base."""
    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported format '{ext or filename}'. "
                f"Supported: {', '.join(SUPPORTED_FORMATS)}."
            ),
        )
    if collection_id is not None and db.get(Collection, collection_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found."
        )

    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )

    return ingest_document(
        db,
        filename=filename,
        data=data,
        content_type=file.content_type or "",
        collection_id=collection_id,
        owner_id=current_user.id,
    )


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    """Return a single document's detail and ingestion status."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        )
    return document


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Delete a document (owner or admin) and drop its vectors from the index."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        )
    if current_user.role != Role.ADMIN.value and document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You may only delete your own documents.",
        )
    db.delete(document)  # cascades to chunks
    db.commit()
    get_store().delete_document(document_id)
    return {"detail": "Document deleted.", "id": document_id}
