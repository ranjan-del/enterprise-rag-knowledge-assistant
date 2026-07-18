"""Pydantic schemas for documents + collections (stub)."""

from pydantic import BaseModel


class DocumentOut(BaseModel):
    # TODO: id, filename, format, status, collection_id, version, created_at.
    id: str


class CollectionOut(BaseModel):
    # TODO: id, name, description, document_count.
    id: str
