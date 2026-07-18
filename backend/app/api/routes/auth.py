"""Auth + user management routes (stub).

MEMORY.md checklist:
- [ ] Auth + user management (roles/permissions)
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
def login() -> dict:
    # TODO: authenticate credentials, issue JWT access token.
    return {"detail": "not implemented"}


@router.post("/register")
def register() -> dict:
    # TODO: create user with hashed password + default role.
    return {"detail": "not implemented"}


@router.get("/me")
def me() -> dict:
    # TODO: return the current authenticated user from the token.
    return {"detail": "not implemented"}


@router.post("/logout")
def logout() -> dict:
    # TODO: invalidate/blacklist token if using stateful sessions.
    return {"detail": "not implemented"}
