"""Run the service: `python -m capper`, the `capper` container's command."""

import uvicorn

from capper.app import create_app

if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
