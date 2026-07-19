"""Entrypoint for the time-deposit service.

Exposes `app` for `uvicorn main:app`, and runs uvicorn directly when
executed as a script (`python main.py`), reading HOST/PORT from the
environment with sane local-dev defaults.
"""

import os

import uvicorn

from adapters.inbound.http.app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
