"""Account use cases: the profile for context, the referral code, and the demo user list."""

from dataclasses import dataclass

from capper.accounts import repository
from capper.db import SessionFactory


@dataclass(frozen=True)
class AccountProfile:
    user_id: int
    name: str
    school_id: int | None
    school_name: str | None
    time_zone: str | None


@dataclass(frozen=True)
class UserListing:
    user_id: int
    name: str
    school_name: str | None


class AccountService:
    def __init__(self, sessions: SessionFactory) -> None:
        self._sessions = sessions

    async def profile(self, user_id: int) -> AccountProfile | None:
        async with self._sessions() as session:
            user = await repository.get_user(session, user_id)
            if user is None:
                return None
            school = (
                await repository.get_school(session, user.school_id) if user.school_id else None
            )
            return AccountProfile(
                user.id,
                user.name,
                user.school_id,
                school.name if school else None,
                user.time_zone,
            )

    async def exists(self, user_id: int) -> bool:
        async with self._sessions() as session:
            return await repository.get_user(session, user_id) is not None

    async def referral_code(self, user_id: int) -> str | None:
        async with self._sessions() as session:
            return await repository.get_referral_code(session, user_id)

    async def list_users(self) -> list[UserListing]:
        async with self._sessions() as session:
            rows = await repository.list_users_with_schools(session)
        return [UserListing(user.id, user.name, school) for user, school in rows]
