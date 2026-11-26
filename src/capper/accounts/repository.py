"""Account queries. Each takes the user ID from the verified identity."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from capper.accounts.models import ReferralCode, School, User


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def get_school(session: AsyncSession, school_id: int) -> School | None:
    return await session.get(School, school_id)


async def get_referral_code(session: AsyncSession, user_id: int) -> str | None:
    return await session.scalar(select(ReferralCode.code).where(ReferralCode.user_id == user_id))


async def list_users_with_schools(session: AsyncSession) -> list[tuple[User, str | None]]:
    """Every user with their school's name, by name then ID (demo sign-in only)."""
    rows = await session.execute(
        select(User, School.name)
        .outerjoin(School, School.id == User.school_id)
        .order_by(User.name, User.id)
    )
    return [(user, school_name) for user, school_name in rows]
