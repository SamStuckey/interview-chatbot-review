"""Print the service's OpenAPI document, to refresh the spec's snapshot. From the repo root:

    docker compose run --rm dev python -m scripts.export_openapi > tests/capper/openapi.json

A spec fails when the committed snapshot no longer matches the app.
"""

import json
import sys

from capper.app import create_app
from capper.config import Settings


def main() -> int:
    settings = Settings()  # pyright: ignore[reportCallIssue]
    app = create_app(settings.model_copy(update={"otlp_endpoint": None}))
    sys.stdout.write(json.dumps(app.openapi(), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
