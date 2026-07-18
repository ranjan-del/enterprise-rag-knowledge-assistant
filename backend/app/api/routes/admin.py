"""Admin routes (stub).

MEMORY.md checklist:
- [ ] Admin: upload, delete, versioning, permissions
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/users")
def list_users() -> dict:
    # TODO: list users (admin only).
    return {"items": []}


@router.put("/users/{user_id}/permissions")
def set_permissions(user_id: str) -> dict:
    # TODO: update a user's roles/permissions.
    return {"id": user_id, "detail": "not implemented"}


@router.post("/documents/{document_id}/versions")
def create_version(document_id: str) -> dict:
    # TODO: create a new version of a document.
    return {"id": document_id, "detail": "not implemented"}


@router.delete("/documents/{document_id}")
def admin_delete_document(document_id: str) -> dict:
    # TODO: hard-delete a document and its vectors (admin override).
    return {"id": document_id, "detail": "not implemented"}
