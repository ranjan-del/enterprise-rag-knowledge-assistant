"""End-to-end ingestion: parse -> chunk -> embed -> persist -> index.

This is the single function the upload endpoint calls. It turns raw uploaded
bytes into a queryable document by running every stage of the pipeline and
keeping the SQL database and the in-memory vector index in sync:

    parse (parser.py) -> chunk (chunk.py) -> embed (embed.py)
      -> persist Document + Chunk rows (SQLite/Postgres)
      -> upsert vectors into the in-memory store

Chunk embeddings are persisted as JSON on the ``chunks`` table, so the in-memory
index can be rebuilt from the database on startup (see
``InMemoryVectorStore.rebuild_from_db``).

MEMORY.md checklist:
- [x] Multi-format upload + parsers (PDF, DOCX, PPTX, TXT, CSV)
- [x] Ingestion pipeline: parse -> chunk -> embed -> vector DB
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ingest import parser
from app.ingest.chunk import chunk_text
from app.ingest.embed import get_embedder
from app.models.document import Chunk, Document
from app.store.vector_store import get_store


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def ingest_document(
    db: Session,
    *,
    filename: str,
    data: bytes,
    content_type: str = "",
    collection_id: int | None = None,
    owner_id: int | None = None,
) -> Document:
    """Ingest one uploaded file and return the persisted ``Document`` row.

    The document is created immediately (status ``processing``) so a row always
    exists; on success it flips to ``ready`` with ``num_chunks`` set, and on any
    parse/index error it flips to ``failed`` with the error recorded. Vectors are
    only added to the in-memory index after the DB transaction commits, so the two
    never drift apart.
    """
    fmt = _extension(filename)
    document = Document(
        filename=filename,
        content_type=content_type,
        format=fmt,
        collection_id=collection_id,
        owner_id=owner_id,
        status="processing",
    )
    db.add(document)
    db.flush()  # assign document.id without committing yet

    try:
        text = parser.parse(filename, data)
        chunks = chunk_text(text)
    except Exception as exc:  # unsupported format, corrupt file, etc.
        document.status = "failed"
        document.error = str(exc)[:500]
        db.commit()
        db.refresh(document)
        return document

    if not chunks:
        document.status = "ready"
        document.num_chunks = 0
        db.commit()
        db.refresh(document)
        return document

    embedder = get_embedder()
    vectors = embedder.embed([c["text"] for c in chunks])

    store_records: list[dict] = []
    for chunk_meta, vector in zip(chunks, vectors):
        embedding = vector.tolist()
        chunk_row = Chunk(
            document_id=document.id,
            collection_id=collection_id,
            chunk_index=chunk_meta["chunk_index"],
            page=chunk_meta["page"],
            char_start=chunk_meta["char_start"],
            char_end=chunk_meta["char_end"],
            text=chunk_meta["text"],
            embedding=embedding,
        )
        db.add(chunk_row)
        db.flush()  # assign chunk_row.id for the vector-store record
        store_records.append(
            {
                "vector": embedding,
                "chunk_id": chunk_row.id,
                "document_id": document.id,
                "collection_id": collection_id,
                "filename": filename,
                "page": chunk_meta["page"],
                "chunk_index": chunk_meta["chunk_index"],
                "text": chunk_meta["text"],
            }
        )

    document.status = "ready"
    document.num_chunks = len(chunks)
    db.commit()
    db.refresh(document)

    # Index only after a successful commit so the vector store mirrors the DB.
    get_store().upsert(store_records)
    return document
