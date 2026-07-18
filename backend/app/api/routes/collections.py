"""Collection management routes (stub).

MEMORY.md checklist:
- [ ] Retriever + search: ... organized into collections
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_collections() -> dict:
    # TODO: list collections for the current user/org.
    return {"items": []}


@router.post("")
def create_collection() -> dict:
    # TODO: create a collection.
    return {"detail": "not implemented"}


@router.get("/{collection_id}")
def get_collection(collection_id: str) -> dict:
    # TODO: return collection + its documents.
    return {"id": collection_id, "detail": "not implemented"}


@router.delete("/{collection_id}")
def delete_collection(collection_id: str) -> dict:
    # TODO: delete collection (and optionally its documents).
    return {"id": collection_id, "detail": "not implemented"}
