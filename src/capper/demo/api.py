"""The demo page and its sign-in routes.

The `/demo` routes let users select an account and obtain a signed session
token without logging in. Authenticated routes verify this token through the
normal authorization path. These sign-in routes are for the demo only.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict

from capper.container import Services

STATIC = Path(__file__).parent / "static"

router = APIRouter(tags=["demo"])


class DemoUser(BaseModel):
    id: int
    name: str
    school: str | None


class SessionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: int


class SessionOut(BaseModel):
    access_token: str
    expires_at: str


def _services(request: Request) -> Services:
    return request.app.state.services


@router.get("/", include_in_schema=False)
async def demo_page() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@router.get("/demo/users")
async def demo_users(request: Request) -> list[DemoUser]:
    """Every user, to pick one to act as."""
    users = await _services(request).accounts.list_users()
    return [DemoUser(id=u.user_id, name=u.name, school=u.school_name) for u in users]


@router.post("/demo/sessions")
async def demo_session(request: Request, body: SessionIn) -> SessionOut:
    """A session for the chosen user: the token the real auth API would have issued."""
    issued = await _services(request).demo_sessions.issue(body.user_id)
    return SessionOut(access_token=issued.access_token, expires_at=issued.expires_at)
