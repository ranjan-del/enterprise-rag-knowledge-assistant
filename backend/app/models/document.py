"""Document + Collection ORM models (stub).

MEMORY.md checklist:
- [ ] Multi-format upload + parsers
- [ ] Retriever + search: ... organized into collections
- [ ] Admin: ... versioning
"""

from app.models.base import Base


class Document(Base):
    __tablename__ = "documents"

    # TODO: id, filename, format, collection_id, owner_id, version, status, created_at.
    __table_args__ = {"extend_existing": True}


class Collection(Base):
    __tablename__ = "collections"

    # TODO: id, name, description, owner_id, created_at.
    __table_args__ = {"extend_existing": True}
