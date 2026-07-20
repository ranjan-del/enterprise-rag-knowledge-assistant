"""End-to-end API tests via FastAPI's TestClient (fully offline).

Covers the full journey: register/login, upload + ingest, semantic + hybrid
search, cited answers, collections, analytics, and admin controls.
"""

from __future__ import annotations

VACATION_DOC = (
    "Company Leave Policy. Full time employees receive twenty five paid "
    "vacation days each year. Unused leave may be carried over to the next "
    "year up to a maximum of five days. Sick leave is separate and unlimited."
).encode("utf-8")

SECURITY_DOC = (
    "Security Guidelines. All administrator accounts must use multi factor "
    "authentication. Passwords rotate every ninety days. Report incidents to "
    "the security team immediately."
).encode("utf-8")


def _upload(client, headers, filename, data, collection_id=None):
    files = {"file": (filename, data, "text/plain")}
    payload = {}
    if collection_id is not None:
        payload["collection_id"] = str(collection_id)
    return client.post(
        "/api/documents/upload", files=files, data=payload, headers=headers
    )


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_login_and_me(client):
    assert client.post(
        "/api/auth/register", json={"email": "jane@example.com", "password": "secret123"}
    ).status_code == 201
    # Duplicate registration is rejected.
    assert client.post(
        "/api/auth/register", json={"email": "jane@example.com", "password": "secret123"}
    ).status_code == 409

    login = client.post(
        "/api/auth/login", data={"username": "jane@example.com", "password": "secret123"}
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "jane@example.com"
    assert me.json()["role"] == "user"


def test_login_rejects_bad_password(client):
    client.post(
        "/api/auth/register", json={"email": "bob@example.com", "password": "secret123"}
    )
    resp = client.post(
        "/api/auth/login", data={"username": "bob@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401


def test_protected_routes_require_auth(client):
    assert client.get("/api/documents").status_code == 401
    assert client.post("/api/search/query", json={"query": "x"}).status_code == 401


def test_upload_ingest_and_query_flow(client, auth_headers):
    up = _upload(client, auth_headers, "leave.txt", VACATION_DOC)
    assert up.status_code == 201, up.text
    doc = up.json()
    assert doc["status"] == "ready"
    assert doc["num_chunks"] >= 1
    assert doc["format"] == "txt"

    # Document appears in the list.
    listing = client.get("/api/documents", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    # Ask a question -> cited answer.
    resp = client.post(
        "/api/search/query",
        json={"query": "How many vacation days do employees get?"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    answer = resp.json()
    assert answer["answer"]
    assert answer["confidence"] > 0
    assert answer["citations"]
    assert answer["source_document"]["filename"] == "leave.txt"
    assert "vacation" in answer["answer"].lower()


def test_semantic_and_hybrid_search(client, auth_headers):
    _upload(client, auth_headers, "leave.txt", VACATION_DOC)
    _upload(client, auth_headers, "security.txt", SECURITY_DOC)

    semantic = client.post(
        "/api/search/semantic",
        json={"query": "multi factor authentication for admins", "mode": "semantic"},
        headers=auth_headers,
    )
    assert semantic.status_code == 200
    results = semantic.json()["results"]
    assert results
    assert results[0]["filename"] == "security.txt"

    hybrid = client.post(
        "/api/search/hybrid",
        json={"query": "multi factor authentication", "mode": "hybrid"},
        headers=auth_headers,
    )
    assert hybrid.status_code == 200
    assert hybrid.json()["results"][0]["filename"] == "security.txt"


def test_unsupported_format_rejected(client, auth_headers):
    resp = _upload(client, auth_headers, "image.png", b"\x89PNG")
    assert resp.status_code == 400


def test_collections_scope_search(client, auth_headers):
    created = client.post(
        "/api/collections",
        json={"name": "HR", "description": "People docs"},
        headers=auth_headers,
    )
    assert created.status_code == 201
    collection_id = created.json()["id"]

    _upload(client, auth_headers, "leave.txt", VACATION_DOC, collection_id=collection_id)
    _upload(client, auth_headers, "security.txt", SECURITY_DOC)  # outside collection

    detail = client.get(f"/api/collections/{collection_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["document_count"] == 1

    scoped = client.post(
        "/api/search/query",
        json={"query": "authentication", "collection_id": collection_id},
        headers=auth_headers,
    )
    assert scoped.status_code == 200
    # Only HR docs are searchable in this collection, so every citation is from it.
    for citation in scoped.json()["citations"]:
        assert citation["filename"] == "leave.txt"


def test_delete_document_removes_from_index(client, auth_headers):
    up = _upload(client, auth_headers, "leave.txt", VACATION_DOC)
    doc_id = up.json()["id"]

    delete = client.delete(f"/api/documents/{doc_id}", headers=auth_headers)
    assert delete.status_code == 200

    resp = client.post(
        "/api/search/query",
        json={"query": "vacation days"},
        headers=auth_headers,
    )
    assert resp.json()["citations"] == []
    assert resp.json()["confidence"] == 0.0


def test_analytics_overview(client, auth_headers):
    _upload(client, auth_headers, "leave.txt", VACATION_DOC)
    client.post(
        "/api/search/query", json={"query": "vacation"}, headers=auth_headers
    )
    overview = client.get("/api/analytics/overview", headers=auth_headers)
    assert overview.status_code == 200
    data = overview.json()
    assert data["documents"] == 1
    assert data["chunks"] >= 1
    assert data["queries"] == 1


def test_admin_controls(client, admin_headers, auth_headers):
    # A regular user cannot list users.
    assert client.get("/api/admin/users", headers=auth_headers).status_code == 403

    users = client.get("/api/admin/users", headers=admin_headers)
    assert users.status_code == 200
    assert any(u["role"] == "admin" for u in users.json())

    # Admin can bump a document version.
    up = _upload(client, admin_headers, "leave.txt", VACATION_DOC)
    doc_id = up.json()["id"]
    bumped = client.post(
        f"/api/admin/documents/{doc_id}/versions", headers=admin_headers
    )
    assert bumped.status_code == 200
    assert bumped.json()["version"] == 2
