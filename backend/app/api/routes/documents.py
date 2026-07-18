"""Document upload + management routes (stub).

MEMORY.md checklist:
- [ ] Multi-format upload + parsers (PDF, DOCX, PPTX, TXT, CSV)
- [ ] Ingestion pipeline: parse -> chunk -> embed -> vector DB
"""

from fastapi import APIRouter, UploadFile

router = APIRouter()


@router.get("")
def list_documents() -> dict:
    # TODO: list documents with metadata + pagination.
    return {"items": [], "total": 0}


@router.post("/upload")
def upload_document(file: UploadFile | None = None) -> dict:
    # TODO: persist file, then trigger ingestion pipeline
    #       (parser -> chunk -> embed -> vector store).
    return {"detail": "not implemented"}


@router.get("/{document_id}")
def get_document(document_id: str) -> dict:
    # TODO: return document detail + ingestion status.
    return {"id": document_id, "detail": "not implemented"}


@router.delete("/{document_id}")
def delete_document(document_id: str) -> dict:
    # TODO: delete document + its vectors from the store.
    return {"id": document_id, "detail": "not implemented"}
