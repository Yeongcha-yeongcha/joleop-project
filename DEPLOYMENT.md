# Backend Deployment Guide

This backend is a FastAPI application with PostgreSQL.

## 1. Runtime Requirements

- Python 3.11+
- PostgreSQL 16 or a compatible managed PostgreSQL database
- Network access to Kakao OAuth endpoints if Kakao login is used

Docker is optional. If Docker is not available on the server, run the app with a Python virtual environment.

## 2. Environment Variables

Create `.env` from `.env.example` and replace secrets before deployment.

```bash
cp .env.example .env
```

Required production values:

```text
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DB_NAME
JWT_SECRET_KEY=a-long-random-secret-at-least-32-characters
KAKAO_CLIENT_ID=...
KAKAO_CLIENT_SECRET=...
KAKAO_REDIRECT_URI=https://your-frontend.example.com/oauth/kakao/callback
CORS_ORIGINS=https://your-frontend.example.com
```

Do not use `change-me` for `JWT_SECRET_KEY` in production.

## 3. Install Without Docker

If Python and venv are already installed:

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

If `python3 -m venv` is missing on Ubuntu:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip
```

If the server has no internet access, prepare wheels on another machine:

```bash
python3 -m pip download -r requirements.txt -d wheelhouse
```

Upload `wheelhouse/` to the server, then install offline:

```bash
python3 -m venv .venv
.venv/bin/pip install --no-index --find-links wheelhouse -r requirements.txt
```

## 4. Database Setup

The app expects PostgreSQL. For local development with Docker:

```bash
docker compose up -d
```

For a managed or already installed PostgreSQL server, create the database and set `DATABASE_URL`.

Run migrations:

```bash
.venv/bin/alembic upgrade head
```

Seed development content:

```bash
.venv/bin/python -m app.seed.seed_data
```

## 5. Run The Server

Development:

```bash
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Production-style single process:

```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Behind Nginx or a platform load balancer, forward external traffic to port `8000`.

## 6. Docker Deployment

Build and run:

```bash
docker build -t story-learning-backend .
docker run --env-file .env -p 8000:8000 story-learning-backend
```

If PostgreSQL is also running through `docker compose`, run migrations inside the container or from the host after setting the same `DATABASE_URL`.

## 7. Verification Checklist

Run automated tests:

```bash
.venv/bin/pytest
```

Start the server:

```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Check process health:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok"}
```

Check database readiness:

```bash
curl -i http://localhost:8000/ready
```

Expected when DB is connected:

```json
{"status":"ok","database":"ok"}
```

Expected when DB is not connected:

```json
{"status":"unavailable","database":"unavailable"}
```

Open Swagger:

```text
http://localhost:8000/docs
```

Check OpenAPI schema:

```bash
curl http://localhost:8000/openapi.json
```

## 8. Presentation Structure

Use this explanation for the project architecture:

- `app/main.py`: creates the FastAPI app, CORS, exception handlers, and health checks.
- `app/api/v1`: HTTP routers. This layer maps API paths to service calls.
- `app/schemas`: Pydantic request/response models and API field aliases.
- `app/services`: business logic for auth, profiles, onboarding, books, learning sessions, speech, evaluation, and rewards.
- `app/models`: SQLAlchemy ORM entities and enums.
- `app/db`: async database engine and session management.
- `alembic`: database migration scripts.
- `app/seed`: idempotent development seed data.
- `tests`: API contract and service behavior tests.

The dependency flow is:

```text
HTTP request -> API router -> dependency injection -> service -> database model -> response schema
```

Health endpoints:

- `/health`: app process is running.
- `/ready`: app can connect to the database.
- `/api/v1/health` and `/api/v1/ready`: versioned equivalents.
