"""FastAPI application entrypoint for the Enterprise RAG Knowledge Assistant.

Wires the API routers together, configures CORS for the Angular frontend, and on
startup: creates the database tables, seeds a bootstrap admin (if configured), and
rebuilds the in-memory vector index from the persisted chunk embeddings so search
works immediately after a restart.

The default configuration is fully offline: SQLite database, deterministic
hashing embedder, in-memory vector store, and an extractive answer generator. No
API key or external service is required to run or test the app.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    admin,
    analytics,
    auth,
    collections,
    documents,
    search,
)
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal, init_db
from app.models.user import Role, User
from app.store.vector_store import get_store

settings = get_settings()


def _seed_admin() -> None:
    """Create the bootstrap admin account once, if configured and absent."""
    if not (settings.first_admin_email and settings.first_admin_password):
        return
    with SessionLocal() as db:
        email = settings.first_admin_email.lower()
        if db.query(User).filter(User.email == email).first() is not None:
            return
        db.add(
            User(
                email=email,
                hashed_password=hash_password(settings.first_admin_password),
                role=Role.ADMIN.value,
            )
        )
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown: prepare the database and warm the vector index."""
    init_db()
    _seed_admin()
    with SessionLocal() as db:
        get_store().rebuild_from_db(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Internal company knowledge system (enterprise RAG).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers. See MEMORY.md "Dashboard" / "Admin" sections.
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(collections.router, prefix="/api/collections", tags=["collections"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/health", tags=["system"])
def health() -> dict:
    """Liveness/readiness probe used by Docker and the hosting platform."""
    return {"status": "ok", "service": settings.app_name, "version": settings.version}
