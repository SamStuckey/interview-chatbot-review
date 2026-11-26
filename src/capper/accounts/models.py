"""Accounts: users and schools (supplied tables) and referral codes."""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from capper.db import Base, UtcDateTime


class School(Base):
    __tablename__ = "Schools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    address: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)


class User(Base):
    __tablename__ = "Users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    school_id: Mapped[int | None] = mapped_column(ForeignKey("Schools.id"))
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[str] = mapped_column(String)
    time_zone: Mapped[str | None] = mapped_column(String)
    """An IANA name such as "America/Los_Angeles"; `None` means the configured default."""


class ReferralCode(Base):
    __tablename__ = "referral_codes"

    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"), primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime)
