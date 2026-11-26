"""Saved user data: guidance notes and the avoid list."""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from capper.db import Base, UtcDateTime


class GuidanceNote(Base):
    __tablename__ = "guidance_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"), index=True)
    text: Mapped[str] = mapped_column(String)
    expires_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime)


class AvoidedProduct(Base):
    __tablename__ = "avoided_products"

    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"), primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("Products.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime)
