# Looks Lab Backend

FastAPI backend for the Looks Lab mobile app.  
It powers onboarding, domain-based AI analysis, image workflows, progress tracking, subscriptions, and auth.

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.x (async) + Alembic
- PostgreSQL
- Google Gemini
- AWS S3 (storage only; no local storage fallback)
- SlowAPI (rate limiting)
- Prometheus FastAPI Instrumentator

## Core Capabilities

- Anonymous onboarding before sign-in
- Google/Apple sign-in with JWT access + refresh token rotation
- Domain-specific question flows
- Async AI processing with persisted job state (multi-worker safe)
- Image upload + scan workflows for image-based domains
- Insight and score persistence
- Progress/completion tracking per domain
- Subscription and IAP endpoints

## Domains

- `skincare`
- `haircare`
- `fashion`
- `workout`
- `diet`
- `height`
- `facial`
- `quit_porn`

## Project Structure

```text
app/
  api/v1/routes/        HTTP routes
  ai/                   domain prompts/processors/config
  core/                 config, db, middleware, storage, exceptions
  data/                 seed JSON (questions)
  models/               SQLAlchemy models
  schemas/              Pydantic schemas
  services/             business logic
  utils/                auth/domain/task helpers
  static/               icons/static assets
  main.py               FastAPI application entrypoint

alembic/                migrations
scripts/                helper scripts (e.g., seeders)
```

## API Base Paths

Primary:

- `/api/v1/...`

Compatibility aliases:

- `/domains/...`
- `/images/...`

## Main API Groups

- **Auth**: `/api/v1/auth/*`
  - Google sign-in, Apple sign-in, refresh, sign-out
- **Onboarding**: `/api/v1/onboarding/*`
  - Questions, sessions, answers, selected domain, payment, link to user
- **Domains**: `/api/v1/domains/*`
  - Questions, answer submission, flow state, progress, retry AI
- **Images**: `/api/v1/images/*`
  - Upload, album, update, delete
- **Insights**: `/api/v1/insights/*`
- **Subscriptions**: `/api/v1/subscriptions/*`
- **IAP**: `/api/v1/iap/*`
- **Workout completion**: `/api/v1/domains/{domain}/completed-exercises`

## Domain Flow Lifecycle

Typical domain flow:

1. Fetch questions
2. Submit answers
3. (Image-based domains) upload required scans
4. Poll flow endpoint until AI completes
5. Consume completed payload + progress blocks

Common statuses:

- `pending` (e.g., waiting for required scans)
- `processing` (AI running)
- `completed`
- some domains may also return `in_progress` during question progression

## Image Upload Notes

Use:

- `POST /api/v1/images/upload`

Send `file` plus optional `domain`, `view`, `image_type` (form-data or query fallback).

Domain-specific view validation:

- `fashion`: `front`, `back`
- `facial`: `front`, `right`, `left`

## Storage

Storage is **S3-only**.

Required runtime config:

- `AWS_S3_BUCKET`
- `AWS_REGION`

Optional:

- `CLOUDFRONT_DOMAIN` (preferred stable public URLs)
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` (if not using IAM role-based auth)

## Security Notes

- Refresh tokens are hashed at rest before DB storage.
- Access is JWT bearer-based on protected routes.
- Domain access is gated by onboarding/subscription state unless explicitly bypassed in config.

## Required Environment Variables

Minimum required to boot:

```env
ENV=development
DATABASE_URI=postgresql+asyncpg://user:pass@localhost:5432/looks_lab
JWT_SECRET=replace-with-long-random-secret
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_CLIENT_ID=your-google-client-id
AWS_S3_BUCKET=your-bucket
AWS_REGION=your-region
```

Common optional variables:

```env
JWT_REFRESH_SECRET=second-long-random-secret
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
TRUSTED_HOSTS=localhost,127.0.0.1
CLOUDFRONT_DOMAIN=cdn.example.com
RATE_LIMIT_PER_MINUTE=60
BYPASS_SUBSCRIPTION_CHECK=false
ENABLE_SECURITY_HEADERS=true
```

## Local Development

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Start dependencies

```bash
docker compose up -d db redis
```

### 3) Run migrations

```bash
alembic upgrade head
```

### 4) Seed questions

```bash
python scripts/seed_questions.py
```

### 5) Run API

```bash
uvicorn app.main:app --reload
```

Docs:

- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Docker

```bash
docker compose up --build
```

App container runs migrations on startup, then serves via Gunicorn + Uvicorn workers.

## Database (Key Tables)

- `users`
- `refresh_tokens`
- `subscriptions`
- `onboarding_sessions`, `onboarding_questions`, `onboarding_answers`
- `domain_questions`, `domain_answers`
- `images`
- `insights`
- `ai_jobs`
- `domain_score_history`
- `workout_completions`
- `daily_recovery`

## Contributing

- Keep route contracts stable or version changes clearly.
- Add/update schemas when payload shape changes.
- Prefer service-layer changes over route-layer logic bloat.
- Run migrations for model changes.
- Validate touched files for lint/type issues before merging.

