"""Demo data on top of the supplied database, idempotently.

Run by the bootstrap.

Adds products (including the ones the mockups show), image URLs, active
promotions, referral codes, purchases spread across schools, time zones for
users who have none, and the seed users' saved guidance and avoid lists.
Running it again changes nothing. Products get only the generic fields the
tools need.
"""

import hashlib
import random
import string
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from capper.accounts.models import ReferralCode, User
from capper.catalog.images import product_image_url
from capper.catalog.models import Product, Promotion, Purchase
from capper.memory.models import AvoidedProduct, GuidanceNote


@dataclass(frozen=True)
class NewProduct:
    name: str
    description: str
    price: float


# Products the mockups show that the supplied catalog lacks, plus a few staples.
EXTRA_PRODUCTS = (
    NewProduct("Corn Tortillas", "Soft corn tortillas for tacos, wraps and quesadillas.", 3.49),
    NewProduct("Sour Cream", "Rich, creamy sour cream for toppings and dips.", 2.89),
    NewProduct("Greek Yogurt Cups", "Creamy Greek yogurt in single-serving fruit flavors.", 5.99),
    NewProduct("Spaghetti Pasta", "Classic dry spaghetti that cooks in about ten minutes.", 1.89),
    NewProduct("Peanut Butter", "Smooth peanut butter for sandwiches and snacks.", 4.29),
    NewProduct("Apple Juice Boxes", "Single-serving 100% apple juice boxes for lunchboxes.", 4.99),
    NewProduct("Whole Wheat Bread", "Soft whole wheat sandwich bread.", 3.29),
    NewProduct("Cheddar Cheese Sticks", "Individually wrapped mild cheddar snack sticks.", 4.59),
)

# (product name, title, description). The first is the mockup's Bonus Caps card.
PROMOTIONS = (
    ("Macaroni & Cheese Box", "Earn 5 extra Caps", "Earn 5 extra Caps on Mac & Cheese this week."),
    ("Fruit Snacks Pouch", "Double Caps", "Earn double Caps on Fruit Snacks Pouches."),
    ("Corn Tortillas", "Taco night bonus", "Earn 3 extra Caps on Corn Tortillas."),
)

NEW_USER_EMAIL = "new.user@example.com"
NEW_USER_NAME = "Nora Newcomer"
# Seed roles taken from the supplied users. Users 1 and 2 share a school, which gives the
# parallel-data pair for cross-account checks.
ESTABLISHED_USER_ID = 1
PARALLEL_USER_ID = 2
GUIDANCE_USER_ID = 3

GUIDANCE = {
    # An allergy note must not turn a product recommendation into a safety guarantee.
    GUIDANCE_USER_ID: ("Allergic to peanuts.", "Kids prefer fruity snacks."),
    ESTABLISHED_USER_ID: ("Shops for a family of four.",),
    PARALLEL_USER_ID: ("Prefers quick weeknight meals.",),
}
AVOIDED = {GUIDANCE_USER_ID: ("Peanut Butter",), PARALLEL_USER_ID: ("Sour Cream",)}

# The supplied users have no time zone. Carton Caps is US-only, so demo users get US
# zones in rotation, which gives local dates and times something real to work with.
US_TIME_ZONES = ("America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles")


def referral_code(user_id: int) -> str:
    """A stable six-character code per user, in the mockup's style (e.g. XY7G4D)."""
    alphabet = string.ascii_uppercase + string.digits
    digest = hashlib.sha256(f"capper-referral-{user_id}".encode()).digest()
    return "".join(alphabet[b % len(alphabet)] for b in digest[:6])


async def seed_products(session: AsyncSession, now: datetime) -> dict[str, int]:
    existing = {p.name: p for p in (await session.scalars(select(Product))).all()}
    for extra in EXTRA_PRODUCTS:
        if extra.name not in existing:
            product = Product(
                name=extra.name,
                description=extra.description,
                price=extra.price,
                created_at=now.replace(tzinfo=None).isoformat(timespec="seconds"),
            )
            session.add(product)
            existing[extra.name] = product
    await session.flush()
    # Every product's image ships in the image; this also corrects an older URL.
    for product in existing.values():
        url = product_image_url(product.name)
        if product.image_url != url:
            product.image_url = url
    return {name: product.id for name, product in existing.items()}


async def seed_promotions(session: AsyncSession, products: dict[str, int], now: datetime) -> None:
    titles = set((await session.scalars(select(Promotion.title))).all())
    for product_name, title, description in PROMOTIONS:
        if title not in titles:
            session.add(
                Promotion(
                    product_id=products[product_name],
                    title=title,
                    description=description,
                    starts_at=now - timedelta(days=7),
                    ends_at=now + timedelta(days=60),
                )
            )


async def seed_new_user(session: AsyncSession) -> int:
    """A brand-new user: no school, purchases, guidance or referral code."""
    user = await session.scalar(select(User).where(User.email == NEW_USER_EMAIL))
    if user is None:
        user = User(
            school_id=None,
            name=NEW_USER_NAME,
            email=NEW_USER_EMAIL,
            created_at=datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds"),
        )
        session.add(user)
        await session.flush()
    return user.id


async def seed_time_zones(session: AsyncSession) -> None:
    """A US time zone for every user without one; a zone already set is left alone."""
    for user in (await session.scalars(select(User).where(User.time_zone.is_(None)))).all():
        user.time_zone = US_TIME_ZONES[user.id % len(US_TIME_ZONES)]


async def seed_referral_codes(session: AsyncSession, new_user_id: int, now: datetime) -> None:
    """Every user except the new user gets a code (the "no code" case)."""
    have = set((await session.scalars(select(ReferralCode.user_id))).all())
    for user_id in (await session.scalars(select(User.id))).all():
        if user_id != new_user_id and user_id not in have:
            session.add(ReferralCode(user_id=user_id, code=referral_code(user_id), created_at=now))


async def seed_purchases(session: AsyncSession, new_user_id: int, products: dict[str, int]) -> None:
    """Purchases for every user but the new one, so schools have something to rank."""
    if await session.scalar(select(func.count()).select_from(Purchase)):
        return
    rng = random.Random(2026)
    product_ids = sorted(products.values())
    favorites = product_ids[:6]  # weighted so popularity has a clear shape
    base = datetime(2026, 9, 1)
    for user_id in sorted((await session.scalars(select(User.id))).all()):
        if user_id == new_user_id:
            continue
        for _ in range(rng.randint(3, 8)):
            pool = favorites if rng.random() < 0.6 else product_ids
            purchased = base + timedelta(days=rng.randint(0, 70), minutes=rng.randint(0, 1440))
            session.add(
                Purchase(
                    user_id=user_id,
                    product_id=rng.choice(pool),
                    quantity=rng.randint(1, 3),
                    purchased_at=purchased.isoformat(timespec="seconds"),
                )
            )


async def seed_memory(session: AsyncSession, products: dict[str, int], now: datetime) -> None:
    for user_id, notes in GUIDANCE.items():
        have = set(
            await session.scalars(select(GuidanceNote.text).where(GuidanceNote.user_id == user_id))
        )
        for text in notes:
            if text not in have:
                session.add(
                    GuidanceNote(
                        user_id=user_id, text=text, expires_at=None, created_at=now, updated_at=now
                    )
                )
    for user_id, names in AVOIDED.items():
        for name in names:
            key = (user_id, products[name])
            if await session.get(AvoidedProduct, key) is None:
                session.add(
                    AvoidedProduct(user_id=user_id, product_id=products[name], created_at=now)
                )


async def seed(session: AsyncSession) -> None:
    now = datetime.now(UTC).replace(microsecond=0)
    async with session.begin():
        products = await seed_products(session, now)
        await seed_promotions(session, products, now)
        new_user_id = await seed_new_user(session)
        await seed_time_zones(session)
        await seed_referral_codes(session, new_user_id, now)
        await seed_purchases(session, new_user_id, products)
        await seed_memory(session, products, now)
