"""Admin routes (admin role required).

Covers the admin controls from MEMORY.md: list and manage users' roles/activation,
bump document versions, and hard-delete any document regardless of owner.

MEMORY.md checklist:
- [x] Admin: upload, delete, versioning, permissions
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_role
from app.models.document import Document
from app.models.user import Role, User
from app.schemas.document import DocumentOut
from app.schemas.user import PermissionUpdate, UserOut
from app.store.vector_store import get_store

router = APIRouter()

_VALID_ROLES = {Role.ADMIN.value, Role.USER.value}


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> list[User]:
    """List all users (admin only)."""
    return db.query(User).order_by(User.created_at.desc()).all()


@router.put("/users/{user_id}/permissions", response_model=UserOut)
def set_permissions(
    user_id: int,
    payload: PermissionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> User:
    """Update a user's role and/or active status (admin only)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    if payload.role is not None:
        if payload.role not in _VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Allowed: {', '.join(sorted(_VALID_ROLES))}.",
            )
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user


@router.post("/documents/{document_id}/versions", response_model=DocumentOut)
def create_version(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> Document:
    """Increment a document's version counter (admin only)."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        )
    document.version += 1
    db.commit()
    db.refresh(document)
    return document


@router.delete("/documents/{document_id}", status_code=status.HTTP_200_OK)
def admin_delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> dict:
    """Hard-delete any document and its vectors (admin override)."""
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found."
        )
    db.delete(document)
    db.commit()
    get_store().delete_document(document_id)
    return {"detail": "Document deleted.", "id": document_id}
