"""Analytics routes (stub).

MEMORY.md checklist:
- [ ] Dashboard: documents, users, search, analytics, collections
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/overview")
def overview() -> dict:
    # TODO: aggregate counts (documents, users, queries) for the dashboard.
    return {"documents": 0, "users": 0, "queries": 0}


@router.get("/usage")
def usage() -> dict:
    # TODO: query volume / popular documents over time.
    return {"series": []}
