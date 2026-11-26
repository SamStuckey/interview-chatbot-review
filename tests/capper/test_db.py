"""Database errors exclude bound values, such as message text."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from capper.db import create_engine


async def test_errors_hide_bound_values() -> None:
    engine = create_engine("sqlite+aiosqlite://")
    try:
        async with engine.connect() as connection:
            with pytest.raises(DBAPIError) as caught:
                await connection.execute(
                    text("SELECT * FROM missing WHERE body = :body"), {"body": "private words"}
                )
    finally:
        await engine.dispose()
    assert "private words" not in str(caught.value)
