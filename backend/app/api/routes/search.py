"""Search + answer routes (stub).

MEMORY.md checklist:
- [ ] Retriever + search: semantic, metadata filter, hybrid; organized into collections
- [ ] Answer generation with confidence, citations, highlighted text, source document
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/query")
def query() -> dict:
    # TODO: run retriever (semantic / metadata filter / hybrid) then LLM answer.
    #       Return answer + confidence + citations + highlighted text + source doc.
    return {"detail": "not implemented"}


@router.post("/semantic")
def semantic_search() -> dict:
    # TODO: embed query -> vector store similarity search.
    return {"results": []}


@router.post("/hybrid")
def hybrid_search() -> dict:
    # TODO: combine keyword (BM25/full-text) + vector scores.
    return {"results": []}
