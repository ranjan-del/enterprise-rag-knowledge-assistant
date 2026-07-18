"""SQLAlchemy declarative base.

MEMORY.md checklist:
- [ ] Auth + user management (roles/permissions)
- [ ] Admin: ... versioning, permissions
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models. TODO: add shared columns/mixins."""
    pass
