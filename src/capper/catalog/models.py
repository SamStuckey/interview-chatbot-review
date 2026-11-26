"""Catalog: products and purchases (supplied tables) and promotions.

The supplied and seeded catalog is the participating catalog. Products
carry only the generic fields the tools need.
"""

from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from capper.db import Base, UtcDateTime


class Product(Base):
    __tablename__ = "Products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[str] = mapped_column(String)
    image_url: Mapped[str | None] = mapped_column(String)


class Purchase(Base):
    __tablename__ = "Purchase_History"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("Products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    purchased_at: Mapped[str] = mapped_column(String)


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("Products.id"))
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    starts_at: Mapped[datetime] = mapped_column(UtcDateTime)
    ends_at: Mapped[datetime] = mapped_column(UtcDateTime)
