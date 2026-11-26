"""Bearer-token verification and the demo sign-in's token issuing.

Capper is a stateless resource server: it verifies the signature (RS256 only),
`exp`, `iss` and `aud` locally against the auth API's public key, and takes
`sub` as the user ID. Login itself is the auth API's job.
"""

from dataclasses import dataclass
from datetime import timedelta

import jwt

from capper.accounts.service import AccountService
from capper.errors import NotAuthenticated, NotFound
from capper.time import Clock

ALGORITHM = "RS256"


@dataclass(frozen=True)
class IssuedToken:
    access_token: str
    expires_at: str


class TokenVerifier:
    def __init__(
        self, public_key: str, *, issuer: str, audience: str, accounts: AccountService
    ) -> None:
        self._public_key = public_key
        self._issuer = issuer
        self._audience = audience
        self._accounts = accounts

    async def verify(self, authorization: str | None) -> int:
        """The verified user ID, or `NotAuthenticated` for any failure (one generic message)."""
        if not authorization:
            raise NotAuthenticated("missing bearer token")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise NotAuthenticated("missing bearer token")
        try:
            claims = jwt.decode(
                token.strip(),
                self._public_key,
                algorithms=[ALGORITHM],
                issuer=self._issuer,
                audience=self._audience,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
            user_id = int(claims["sub"])
        except (jwt.PyJWTError, ValueError, TypeError) as error:
            raise NotAuthenticated("invalid or expired token") from error
        if not await self._accounts.exists(user_id):
            raise NotAuthenticated("invalid or expired token")
        return user_id


class DemoSessionIssuer:
    """Stands in for the result of the hypothetical auth API's login.

    It issues exactly the token the real auth API would, signed with the dev
    private key. Everything after that goes through `TokenVerifier`.
    """

    def __init__(
        self,
        private_key: str,
        *,
        issuer: str,
        audience: str,
        lifetime: timedelta,
        clock: Clock,
        accounts: AccountService,
    ) -> None:
        self._private_key = private_key
        self._issuer = issuer
        self._audience = audience
        self._lifetime = lifetime
        self._clock = clock
        self._accounts = accounts

    async def issue(self, user_id: int) -> IssuedToken:
        if not await self._accounts.exists(user_id):
            raise NotFound(f"user {user_id} not found")
        now = self._clock()
        expires = now + self._lifetime
        token = jwt.encode(
            {
                "sub": str(user_id),
                "iss": self._issuer,
                "aud": self._audience,
                "iat": now,
                "exp": expires,
            },
            self._private_key,
            algorithm=ALGORITHM,
        )
        return IssuedToken(token, expires.isoformat())
