"""Bearer-token validation and demo session tokens."""

import base64
import hashlib
import hmac
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
import pytest

from capper.accounts.service import AccountService
from capper.auth.service import DemoSessionIssuer, TokenVerifier
from capper.db import create_engine, create_session_factory
from capper.errors import NotAuthenticated, NotFound
from tests.support import AUDIENCE, ESTABLISHED_USER, ISSUER, Keys, database_url, make_keys, token


@pytest.fixture
async def accounts(db_path: Path) -> AsyncIterator[AccountService]:
    engine = create_engine(database_url(db_path))
    yield AccountService(create_session_factory(engine))
    await engine.dispose()


@pytest.fixture
def verifier(keys: Keys, accounts: AccountService) -> TokenVerifier:
    return TokenVerifier(
        keys.public_path.read_text(), issuer=ISSUER, audience=AUDIENCE, accounts=accounts
    )


def _unsigned(payload: dict[str, Any]) -> str:
    def part(data: dict[str, Any]) -> str:
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")

    return f"{part({'alg': 'none', 'typ': 'JWT'})}.{part(payload)}."


async def test_a_valid_token_yields_its_user(verifier: TokenVerifier, keys: Keys) -> None:
    assert await verifier.verify(f"Bearer {token(keys, ESTABLISHED_USER)}") == ESTABLISHED_USER


@pytest.mark.parametrize("header", [None, "", "Bearer", "Bearer   ", "Basic abc", "not-a-token"])
async def test_missing_or_malformed_headers_are_rejected(
    verifier: TokenVerifier, header: str | None
) -> None:
    with pytest.raises(NotAuthenticated):
        await verifier.verify(header)


async def test_a_malformed_token_is_rejected(verifier: TokenVerifier) -> None:
    with pytest.raises(NotAuthenticated):
        await verifier.verify("Bearer abc.def.ghi")


async def test_a_token_signed_by_another_key_is_rejected(
    verifier: TokenVerifier, tmp_path: Path
) -> None:
    other = make_keys(tmp_path / "other")
    with pytest.raises(NotAuthenticated):
        await verifier.verify(f"Bearer {token(other, ESTABLISHED_USER)}")


async def test_alg_none_is_rejected(verifier: TokenVerifier) -> None:
    now = datetime.now(UTC)
    unsigned = _unsigned(
        {
            "sub": str(ESTABLISHED_USER),
            "iss": ISSUER,
            "aud": AUDIENCE,
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        }
    )
    with pytest.raises(NotAuthenticated):
        await verifier.verify(f"Bearer {unsigned}")


async def test_algorithm_confusion_is_rejected(verifier: TokenVerifier, keys: Keys) -> None:
    """An HS256 token keyed with the public key must not pass as RS256."""
    expires = int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())
    claims = {"sub": str(ESTABLISHED_USER), "iss": ISSUER, "aud": AUDIENCE, "exp": expires}
    header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').decode().rstrip("=")
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    signature = hmac.new(
        keys.public_path.read_bytes(), f"{header}.{body}".encode(), hashlib.sha256
    ).digest()
    forged = f"{header}.{body}.{base64.urlsafe_b64encode(signature).decode().rstrip('=')}"
    with pytest.raises(NotAuthenticated):
        await verifier.verify(f"Bearer {forged}")


@pytest.mark.parametrize(
    "claims",
    [
        {"exp": datetime.now(UTC) - timedelta(minutes=1)},
        {"iss": "someone-else"},
        {"aud": "another-service"},
    ],
    ids=["expired", "wrong-iss", "wrong-aud"],
)
async def test_bad_claims_are_rejected(
    verifier: TokenVerifier, keys: Keys, claims: dict[str, Any]
) -> None:
    with pytest.raises(NotAuthenticated):
        await verifier.verify(f"Bearer {token(keys, ESTABLISHED_USER, **claims)}")


async def test_a_token_without_exp_is_rejected(verifier: TokenVerifier, keys: Keys) -> None:
    payload = {"sub": str(ESTABLISHED_USER), "iss": ISSUER, "aud": AUDIENCE}
    raw = jwt.encode(payload, keys.private_pem, algorithm="RS256")
    with pytest.raises(NotAuthenticated):
        await verifier.verify(f"Bearer {raw}")


async def test_a_valid_token_for_an_unknown_user_is_rejected(
    verifier: TokenVerifier, keys: Keys
) -> None:
    with pytest.raises(NotAuthenticated):
        await verifier.verify(f"Bearer {token(keys, 999_999)}")


async def test_a_demo_session_token_passes_the_same_verification(
    verifier: TokenVerifier, keys: Keys, accounts: AccountService
) -> None:
    issuer = DemoSessionIssuer(
        keys.private_pem,
        issuer=ISSUER,
        audience=AUDIENCE,
        lifetime=timedelta(minutes=60),
        clock=lambda: datetime.now(UTC),
        accounts=accounts,
    )
    issued = await issuer.issue(ESTABLISHED_USER)
    assert await verifier.verify(f"Bearer {issued.access_token}") == ESTABLISHED_USER
    with pytest.raises(NotFound):
        await issuer.issue(999_999)
