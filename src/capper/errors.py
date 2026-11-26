"""Domain exceptions, mapped to HTTP responses in one place.

Services raise these; they carry no HTTP types. `register_error_handlers`
(called by the composition root) turns each into the JSON error body
`{"error": {"code", "message"}}`.
"""

from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class DomainError(Exception):
    """Base class: a stable machine-readable code and a user-safe message."""

    status_code = 400
    code = "bad_request"

    def __init__(self, message: str, **details: str | None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotAuthenticated(DomainError):
    status_code = 401
    code = "not_authenticated"


class NotFound(DomainError):
    status_code = 404
    code = "not_found"


class TurnInProgress(DomainError):
    status_code = 409
    code = "turn_in_progress"


class LimitReached(DomainError):
    """A saved-guidance or avoid-list cap is full."""

    status_code = 409
    code = "limit_reached"


class InvalidRequest(DomainError):
    status_code = 422
    code = "invalid_request"


class IdempotencyKeyReused(DomainError):
    status_code = 422
    code = "idempotency_key_reused"


def error_body(code: str, message: str, **details: str | None) -> dict[str, dict[str, str | None]]:
    return {"error": {"code": code, "message": message, **details}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error(_request: Request, exc: DomainError) -> JSONResponse:  # pyright: ignore[reportUnusedFunction]
        headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, NotAuthenticated) else None
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, **exc.details),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:  # pyright: ignore[reportUnusedFunction]
        errors = cast(list[dict[str, Any]], exc.errors())
        first: dict[str, Any] = errors[0] if errors else {}
        location = ".".join(str(part) for part in first.get("loc", ()))
        message = (
            f"{location}: {first.get('msg', 'invalid request')}" if location else "invalid request"
        )
        return JSONResponse(status_code=422, content=error_body("invalid_request", message))
