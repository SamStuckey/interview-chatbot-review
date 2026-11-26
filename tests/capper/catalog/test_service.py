"""Catalog filtering, cards built from records, and cursor pagination."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import pytest

from capper.catalog.service import CatalogService
from capper.db import create_engine, create_session_factory
from capper.errors import InvalidRequest
from tests.support import ESTABLISHED_USER, GUIDANCE_USER, PARALLEL_USER, database_url

PEANUT_BUTTER = "Peanut Butter"  # on GUIDANCE_USER's avoid list (seed)


@pytest.fixture
async def catalog(db_path: Path) -> AsyncIterator[CatalogService]:
    engine = create_engine(database_url(db_path))
    yield CatalogService(create_session_factory(engine), lambda: datetime.now(UTC))
    await engine.dispose()


async def _all_names(catalog: CatalogService, user_id: int, query: str | None = None) -> list[str]:
    names: list[str] = []
    cursor = None
    while True:
        page = await catalog.search(user_id, query, 3, cursor)
        names += [p.name for p in page.items]
        cursor = page.next_cursor
        if cursor is None:
            return names


async def test_paging_walks_every_product_once_in_a_stable_order(catalog: CatalogService) -> None:
    first = await catalog.search(ESTABLISHED_USER, None, 3, None)
    names = await _all_names(catalog, ESTABLISHED_USER)
    assert len(names) == first.total_count == len(set(names))
    assert names == sorted(names)
    assert first.next_cursor is not None


async def test_the_last_page_has_no_cursor(catalog: CatalogService) -> None:
    page = await catalog.search(ESTABLISHED_USER, None, 50, None)
    assert page.next_cursor is None
    assert len(page.items) == page.total_count


async def test_search_matches_name_and_description_case_insensitively(
    catalog: CatalogService,
) -> None:
    by_name = await catalog.search(ESTABLISHED_USER, "CEREAL", 10, None)
    assert {p.name for p in by_name.items} >= {"Frosted Flakes Cereal", "Granola Cereal Bars"}
    by_description = await catalog.search(ESTABLISHED_USER, "lunchboxes", 10, None)
    assert [p.name for p in by_description.items] == ["Apple Juice Boxes"]


async def test_search_treats_wildcard_characters_as_text(catalog: CatalogService) -> None:
    # One description holds a literal "%" ("100% apple juice"); as a wildcard, "%" matched all.
    percent = await catalog.search(ESTABLISHED_USER, "%", 10, None)
    assert [p.name for p in percent.items] == ["Apple Juice Boxes"]
    assert (await catalog.search(ESTABLISHED_USER, "_", 10, None)).items == []


async def test_avoided_products_never_appear(catalog: CatalogService) -> None:
    assert PEANUT_BUTTER not in await _all_names(catalog, GUIDANCE_USER)
    assert PEANUT_BUTTER in await _all_names(catalog, ESTABLISHED_USER)
    popular = await catalog.popular(GUIDANCE_USER, None, 50, None)
    assert PEANUT_BUTTER not in {p.name for p in popular.page.items}


async def test_a_bad_cursor_or_limit_is_an_explicit_error(catalog: CatalogService) -> None:
    with pytest.raises(InvalidRequest):
        await catalog.search(ESTABLISHED_USER, None, 10, "not-a-cursor")
    with pytest.raises(InvalidRequest):
        await catalog.search(ESTABLISHED_USER, None, 0, None)
    capped = await catalog.search(ESTABLISHED_USER, None, 500, None)
    assert len(capped.items) <= 50


async def test_promotions_are_active_and_ordered_by_end_date(catalog: CatalogService) -> None:
    page = await catalog.promotions(ESTABLISHED_USER, 2, None)
    assert page.total_count == 3
    assert page.next_cursor is not None
    rest = await catalog.promotions(ESTABLISHED_USER, 2, page.next_cursor)
    ordered = [*page.items, *rest.items]
    assert [p.id for p in ordered] == sorted(p.id for p in ordered)  # same end date: by ID
    assert rest.next_cursor is None


async def test_purchases_are_newest_first_and_only_the_users(catalog: CatalogService) -> None:
    page = await catalog.purchases(ESTABLISHED_USER, 50, None)
    dates = [p.purchased_at for p in page.items]
    assert dates == sorted(dates, reverse=True)
    other = await catalog.purchases(PARALLEL_USER, 50, None)
    assert page.items != other.items


async def test_popular_products_use_the_school_or_overall(catalog: CatalogService) -> None:
    at_school = await catalog.popular(ESTABLISHED_USER, 7, 5, None)
    overall = await catalog.popular(ESTABLISHED_USER, None, 5, None)
    assert at_school.basis == "school" and overall.basis == "overall"
    counts = [p.purchase_count for p in overall.page.items]
    assert counts == sorted(counts, reverse=True)
    assert overall.page.total_count >= len(overall.page.items)


async def test_cards_are_built_from_records_in_the_given_order(catalog: CatalogService) -> None:
    items = await catalog.product_cards(ESTABLISHED_USER, [3, 1])
    assert [item.id for item in items] == [3, 1]
    assert items[0].name == "Macaroni & Cheese Box"
    assert items[0].image_url


async def test_unknown_or_avoided_card_ids_are_refused(catalog: CatalogService) -> None:
    with pytest.raises(InvalidRequest, match="unknown product IDs"):
        await catalog.product_cards(ESTABLISHED_USER, [1, 999])
    names = await catalog.search(ESTABLISHED_USER, PEANUT_BUTTER, 1, None)
    with pytest.raises(InvalidRequest, match="avoid list"):
        await catalog.product_cards(GUIDANCE_USER, [names.items[0].id])
    with pytest.raises(InvalidRequest, match="unknown promotion IDs"):
        await catalog.promotion_cards(ESTABLISHED_USER, [999])
