"""The `init` service's bootstrap. Idempotent: safe on every `docker compose up`.

In order: the dev key pair, the supplied database, migrations, seed data, and
the content shipped in the image. Each step leaves existing work alone, so a
second run changes nothing unless the image brought new content.

The key pair stands in for the hypothetical auth API's signing key: the
private key signs demo sessions, the public key verifies every
request. The supplied database and the seed data are the demo's data;
a real deployment would start from the app's own database instead.
"""

import asyncio
import shutil
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy.engine import make_url

from capper.config import StorageSettings
from capper.db import create_engine, create_session_factory
from ingestion import ingest
from scripts.seed import seed

FIXTURE = Path("supporting-files/Carton Caps Data.sqlite")
MANIFEST = Path("content/manifest.toml")
ALEMBIC_INI = Path("alembic.ini")


def create_keys(private_path: Path, public_path: Path) -> str:
    if private_path.exists() and public_path.exists():
        return "keys: present"
    private_path.parent.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    private_path.chmod(0o600)
    public_path.write_bytes(
        key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )
    return "keys: created"


def copy_fixture(database_url: str) -> str:
    target = Path(make_url(database_url).database or "")
    if target.exists():
        return "database: present"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURE, target)
    return "database: copied from the supplied fixture"


def migrate() -> str:
    command.upgrade(Config(str(ALEMBIC_INI)), "head")
    return "migrations: at head"


async def seed_and_ingest(database_url: str) -> list[str]:
    engine = create_engine(database_url)
    try:
        sessions = create_session_factory(engine)
        async with sessions() as session:
            await seed(session)
        async with sessions() as session:
            published = await ingest(session, MANIFEST)
    finally:
        await engine.dispose()
    changed = ", ".join(published.published + published.deactivated) or "no changes"
    return ["seed data: in place", f"content {published.version}: {changed}"]


def main() -> int:
    storage = StorageSettings()
    steps = [
        create_keys(Path(storage.jwt_private_key_path), Path(storage.jwt_public_key_path)),
        copy_fixture(storage.database_url),
        migrate(),
        *asyncio.run(seed_and_ingest(storage.database_url)),
    ]
    for step in steps:
        print(f"bootstrap: {step}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
