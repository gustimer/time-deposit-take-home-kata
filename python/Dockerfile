# Minimal, reproducible image for the FastAPI time-deposit service.
# Uses uv (already the project's dependency manager) for a fast, locked install.
FROM python:3.12-slim

# uv installed via the official static binary (no extra build deps needed).
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

WORKDIR /app

# Copy dependency manifests first for better layer caching.
COPY pyproject.toml uv.lock ./

# Install only runtime dependencies (no dev/test deps) into a project-local venv.
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application source.
COPY . .

RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
