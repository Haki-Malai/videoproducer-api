# SkyFlow API

SkyFlow API is a FastAPI service for managing drone flight videos and pilot information. The project uses Poetry for dependency management and provides a Docker-based local stack (Postgres + API + nginx) for quick startup.

## Prerequisites

- Python 3.12 (or at least 3.10 compatible with Poetry constraints)
- [Poetry](https://python-poetry.org/docs/#installation)
- Docker and Docker Compose (optional, for running the full stack)

## Environment Configuration

Configuration is read from environment variables defined in `.env`. Start from the provided example:

```bash
cp .env.example .env
```

Edit `.env` with your own secrets. The available variables are:

| Variable | Description |
| --- | --- |
| `API_PORT` | Port the FastAPI application listens on internally and inside Docker (default `8765`). |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` | Database connection credentials used by the application and Postgres container. |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Default admin credentials seeded/used by the service. |
| `SECRET_KEY` | Secret used for signing JWT tokens. Generate a long random string before running in production. |

When running commands locally through Poetry, keep `POSTGRES_HOST=localhost` (the default) so they connect to the Postgres port exposed on your machine. The Docker Compose configuration overrides this value inside the API container to `postgres`, so you do not need to maintain a separate `.env` file for container workflows.

> The `API_PORT` value is used everywhere (app server, Docker, nginx reverse proxy), so you only need to change it in `.env` for the entire stack to follow.

## Local Development (Poetry)

```bash
poetry install
poetry run uvicorn core.server:app --host 0.0.0.0 --port ${API_PORT:-8765}
```

Alternatively, run the convenience entry point that mirrors production flags:

```bash
poetry run python main.py
```

## Generating Demo Data

Populate the local database with demo users and flights using the CLI:

```bash
poetry run python -m cli fake generate --users 5 --flights-per-user 3
```

All generated users share the same password (override with `--password`) so you can quickly log in with any account while showcasing the product.

## Submitting Flights

Flights no longer require uploading raw footage to the API. Instead, provide a public YouTube URL alongside the usual metadata:

```bash
curl -X POST http://localhost:8765/api/v1/flights \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
        "video_url": "https://youtu.be/abc123xyz78",
        "lat": 51.5,
        "lng": -0.12,
        "title": "Evening cruise",
        "duration_seconds": 180
      }'
```

The API stores the YouTube link directly and immediately exposes it to moderators and the public flight listing once approved.

## Docker Workflow

To start Postgres, the API, and nginx locally:

```bash
docker compose up --build
```

The nginx container proxies port `80` on your machine to the API service running on `API_PORT` inside the network. Updating `.env` automatically updates every component the next time you run `docker compose up`.

## Running Tests

```bash
poetry run pytest
```

## Project Layout

- `core/` – configuration, database, and shared infrastructure.
- `api/` – FastAPI routers and endpoints.
- `app/` – domain models and business logic.
- `tests/` – unit and API tests run via Pytest.

## Additional Notes

- When deploying, base your secrets file on `.env.example` but never commit the actual `.env`.
