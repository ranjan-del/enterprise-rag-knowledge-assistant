"""FastAPI application entrypoint for the Enterprise RAG Knowledge Assistant.

Wires together the API routers and exposes a health probe.

MEMORY.md checklist:
- [ ] `docker compose up` brings up full stack (api, db, vector store, frontend)
- [ ] API documentation
"""

from fastapi import FastAPI

from app.core.config import get_settings
from app.api.routes import (
    admin,
    analytics,
    auth,
    collections,
    documents,
    search,
)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Internal company knowledge system (enterprise RAG).",
)

# TODO: configure CORS, auth middleware, and exception handlers.

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
