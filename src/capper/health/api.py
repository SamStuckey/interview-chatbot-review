"""`GET /healthz` for the Compose health check. No token needed."""

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthOut(BaseModel):
    status: str


@router.get("/healthz", responses={503: {"model": HealthOut}})
async def healthz(request: Request, response: Response) -> HealthOut:
    if await request.app.state.services.health.database_ready():
        return HealthOut(status="ok")
    response.status_code = 503
    return HealthOut(status="unavailable")
