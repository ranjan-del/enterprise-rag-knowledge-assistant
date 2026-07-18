"""User ORM model (stub).

MEMORY.md checklist:
- [ ] Auth + user management (roles/permissions)
"""

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    # TODO: id, email, hashed_password, role, created_at, is_active columns.
    __table_args__ = {"extend_existing": True}
