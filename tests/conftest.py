"""Shared fixtures. No spec ever reaches a real model."""

import shutil
from pathlib import Path

import pytest
from pydantic_ai import models

from tests.support import Keys, build_template, make_keys

models.ALLOW_MODEL_REQUESTS = False


@pytest.fixture(scope="session")
def template_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return build_template(tmp_path_factory.mktemp("template"))


@pytest.fixture(scope="session")
def keys(tmp_path_factory: pytest.TempPathFactory) -> Keys:
    return make_keys(tmp_path_factory.mktemp("keys"))


@pytest.fixture
def db_path(template_db: Path, tmp_path: Path) -> Path:
    """A fresh copy of the seeded database for this test."""
    path = tmp_path / "capper.db"
    shutil.copyfile(template_db, path)
    return path
