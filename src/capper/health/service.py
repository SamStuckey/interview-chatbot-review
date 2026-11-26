"""Readiness: the service is healthy when its database answers."""

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from capper.db import SessionFactory

logger = logging.getLogger(__name__)


class HealthService:
    def __init__(self, sessions: SessionFactory) -> None:
        self._sessions = sessions

    async def database_ready(self) -> bool:
        try:
            async with self._sessions() as session:
                await session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            logger.exception("health check: the database didn't answer")
            return False
        return True
