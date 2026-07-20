"""Unit tests for the offline ingestion + retrieval building blocks.

These exercise the deterministic core (parse, chunk, embed, vector store,
retrievers, answer assembly) without a database or the API layer.
"""

from __future__ import annotations

import numpy as np

from app.generate.answer import build_answer
from app.ingest.chunk import chunk_text
from app.ingest.embed import HashingEmbedder
from app.ingest.parser import PAGE_BREAK, parse
from app.retrieve.hybrid import HybridRetriever
from app.retrieve.retriever import Retriever
from app.store.vector_store import InMemoryVectorStore


def _build_store(docs: list[str], embedder: HashingEmbedder) -> InMemoryVectorStore:
    store = InMemoryVectorStore(dim=embedder.dim)
    vectors = embedder.embed(docs)
    records = [
        {
            "vector": vec.tolist(),
            "chunk_id": i,
            "document_id": 1,
            "collection_id": None,
            "filename": "kb.txt",
            "page": 1,
            "chunk_index": i,
            "text": text,
        }
        for i, (text, vec) in enumerate(zip(docs, vectors))
    ]
    store.upsert(records)
    return store


def test_parse_txt_and_csv():
    assert parse("notes.txt", b"hello world") == "hello world"
    csv_text = parse("data.csv", b"name,role\nAda,engineer\n")
    assert "name: Ada" in csv_text
    assert "role: engineer" in csv_text


def test_chunk_respects_page_breaks_and_overlap():
    text = f"page one content{PAGE_BREAK}page two content"
    chunks = chunk_text(text, chunk_size=50, overlap=10)
    pages = {c["page"] for c in chunks}
    assert pages == {1, 2}
    assert all(c["text"] for c in chunks)


def test_embedder_is_deterministic_and_normalized():
    embedder = HashingEmbedder(dim=64)
    a = embedder.embed_one("the quick brown fox")
    b = embedder.embed_one("the quick brown fox")
    assert np.allclose(a, b)  # reproducible across calls
    assert abs(float(np.linalg.norm(a)) - 1.0) < 1e-5  # unit length


def test_semantic_retriever_ranks_relevant_chunk_first():
    embedder = HashingEmbedder(dim=256)
    docs = [
        "The vacation policy grants employees twenty paid leave days per year.",
        "The office cafeteria serves lunch between noon and two in the afternoon.",
        "Expense reports must be submitted within thirty days of travel.",
    ]
    store = _build_store(docs, embedder)
    retriever = Retriever(store=store, embedder=embedder)

    results = retriever.retrieve("How many paid leave days do employees get?", top_k=3)
    assert results
    assert "leave days" in results[0]["text"]
    assert results[0]["score"] >= results[-1]["score"]


def test_hybrid_retriever_returns_ranked_results():
    embedder = HashingEmbedder(dim=256)
    docs = [
        "Kubernetes handles container orchestration across the cluster.",
        "The quarterly revenue report shows growth in the cloud segment.",
        "Onboarding new engineers takes about two weeks.",
    ]
    store = _build_store(docs, embedder)
    hybrid = HybridRetriever(store=store, embedder=embedder, alpha=0.5)

    results = hybrid.retrieve("container orchestration cluster", top_k=3)
    assert results
    assert "Kubernetes" in results[0]["text"]
    assert "hybrid_score" in results[0]


def test_build_answer_produces_citations_confidence_and_highlights():
    embedder = HashingEmbedder(dim=256)
    docs = [
        "The security policy requires multi factor authentication for all admins.",
        "Coffee is available on every floor of the building.",
    ]
    store = _build_store(docs, embedder)
    retriever = Retriever(store=store, embedder=embedder)

    retrieved = retriever.retrieve("What authentication is required for admins?", top_k=2)
    result = build_answer("What authentication is required for admins?", retrieved)

    assert result["answer"]
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["citations"]
    assert result["citations"][0]["marker"] == "[1]"
    assert result["source_document"]["filename"] == "kb.txt"
    # At least one query term should be highlighted in the top chunk.
    assert any(h["term"] in ("authentication", "admins", "required") for h in result["highlights"])


def test_build_answer_handles_no_results():
    result = build_answer("anything", [])
    assert result["confidence"] == 0.0
    assert result["citations"] == []
    assert result["source_document"] is None
