"""The FastAPI dependency turning the bearer token into the verified user ID."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from capper.auth.service import TokenVerifier

# Declares bearer auth in the OpenAPI document; verification itself is `TokenVerifier`'s.
bearer = HTTPBearer(auto_error=False, description="An access token from the Carton Caps auth API")


def _verifier(request: Request) -> TokenVerifier:
    return request.app.state.services.verifier


async def current_user_id(
    verifier: Annotated[TokenVerifier, Depends(_verifier)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> int:
    """The only source of `user_id` for every route."""
    header = f"{credentials.scheme} {credentials.credentials}" if credentials else None
    return await verifier.verify(header)


CurrentUser = Annotated[int, Depends(current_user_id)]
