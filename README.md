# Looks Lab Backend API

AI-powered FastAPI backend for the Looks Lab wellness platform.

The backend supports:
- anonymous onboarding before authentication
- Google and Apple sign-in
- one purchased wellness domain per onboarding session
- domain-specific question flows
- AI-generated insights powered by Google Gemini
- image upload and analysis flows for image-based domains
- progress, insight, and workout tracking

## Tech Stack
- Python 3.12
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Alembic
- Google Gemini
- AWS S3 storage
- SlowAPI rate limiting
- Prometheus FastAPI Instrumentator

## Project Structure
```text
app/
  api/v1/routes/        HTTP endpoints
  ai/                   Gemini prompts, processors, configs
  core/                 config, db, middleware, storage, errors
  data/                 seed JSON for onboarding and domain questions
  models/               SQLAlchemy models
  schemas/              Pydantic schemas
  services/             business logic
  static/               static assets and icons
  utils/                auth, domain, token, and helper utilities
  main.py               FastAPI app entry point
alembic/                database migrations
scripts/                helper scripts, including question seeding
README.md               project overview
```

## Runtime Architecture
```text
Client App
  -> FastAPI routes
  -> service layer
  -> SQLAlchemy models / PostgreSQL
  -> external services
       - Google Gemini
       - AWS S3 storage
       - Google / Apple auth verification
       - Open Food Facts barcode API
```

## Main End-to-End Flow
1. Client creates an anonymous onboarding session.
2. Client submits onboarding answers.
3. Client selects a domain.
4. Client confirms payment for that onboarding session.
5. User signs in with Google or Apple.
6. Client links the completed onboarding session to the authenticated user.
7. User answers domain-specific questions and may upload domain images.
8. After all required answers are submitted, AI processing starts.
9. AI output is saved as an insight and score history.
10. Client fetches insights, progress, images, and workout stats.

## Current Domains
- `skincare`
- `haircare`
- `fashion`
- `workout`
- `diet`
- `height`
- `facial`
- `quit_porn`

## Authentication
Authentication is token-based.

Supported sign-in providers:
- Google
- Apple

Endpoints:
```text
POST /api/v1/auth/google
POST /api/v1/auth/apple
POST /api/v1/auth/refresh
POST /api/v1/auth/sign-out
```

Notes:
- access tokens are JWTs
- refresh tokens are hashed before storing in the database
- protected routes use Bearer auth

## Onboarding Flow
Onboarding is intentionally available before login.

Endpoints:
```text
GET   /api/v1/onboarding/questions
POST  /api/v1/onboarding/sessions
POST  /api/v1/onboarding/sessions/{session_id}/answers
GET   /api/v1/onboarding/sessions/{session_id}/answers
GET   /api/v1/onboarding/domains
POST  /api/v1/onboarding/sessions/{session_id}/domain?domain={domain}
POST  /api/v1/onboarding/sessions/{session_id}/payment
PATCH /api/v1/onboarding/sessions/{session_id}/link
GET   /api/v1/onboarding/users/me/answers
GET   /api/v1/onboarding/users/me/wellness
```

What it does:
- creates anonymous onboarding sessions
- stores general onboarding answers
- records the selected paid domain
- marks payment confirmation on the onboarding session
- links the onboarding session to the authenticated user after sign-in
- exposes wellness summary fields like height, weight, sleep, water, and daily quote

## Domain Question and AI Flow
Core domain routes live under `/api/v1/domains`.

Endpoints:
```text
GET    /api/v1/domains/progress/overview
GET    /api/v1/domains/explore
GET    /api/v1/domains/{domain}/progress/graph?period=weekly|monthly|yearly
GET    /api/v1/domains/{domain}/questions
GET    /api/v1/domains/{domain}/flow
POST   /api/v1/domains/{domain}/answers
POST   /api/v1/domains/{domain}/answers/bulk
GET    /api/v1/domains/{domain}/answers
DELETE /api/v1/domains/{domain}/answers
POST   /api/v1/domains/{domain}/retry-ai
```

Flow behavior:
1. Client fetches questions for a domain.
2. Client submits answers one-by-one or in bulk.
3. Backend stores answers in `domain_answers`.
4. When all questions are answered, backend starts AI processing.
5. While AI is running, the flow returns `status=processing`.
6. When complete, the flow returns `status=completed` plus domain-specific AI fields.
7. AI output is stored in `insights` and score history is stored in `domain_score_history`.

Important note:
- domain access is gated by onboarding session state plus subscription state
- by default, only the domain selected during onboarding is accessible

## Image Upload and Analysis
Image routes live under `/api/v1/images`.

Endpoints:
```text
POST   /api/v1/images/upload/simple
POST   /api/v1/images/upload
GET    /api/v1/images/album
GET    /api/v1/images/{image_id}
PATCH  /api/v1/images/{image_id}
DELETE /api/v1/images/{image_id}
```

There is also a diet-specific image analysis route:
```text
POST /api/v1/domains/diet/foods/analyze
```

High-level behavior:
- files are validated before storage
- storage is S3-only
- images are saved in the `images` table with domain, view, type, and status metadata
- image-heavy domains such as `skincare`, `haircare`, `facial`, and `fashion` start in `processing` state
- those image-heavy domains may trigger quick preview analysis and later full domain AI analysis
- diet food analysis uploads an image, stores it, and then sends the image URL to Gemini-based food analysis

## Workout and Diet AI Generators
These are separate from the domain completion flow.

Workout endpoint:
```text
POST /api/v1/domains/workout/generate-plan
```

Diet endpoint:
```text
POST /api/v1/domains/diet/generate-meal-plan
```

These routes:
- use current user data plus onboarding context
- generate one-off structured plans
- return plan payloads directly to the client
- do not replace the main domain insight flow

## Workout Completion and Recovery Tracking
Routes:
```text
GET /api/v1/domains/workout/weekly-summary
GET /api/v1/domains/workout/progress-summary?period=week|month|year
GET /api/v1/domains/workout/recovery-checklist?date=YYYY-MM-DD
PUT /api/v1/domains/workout/recovery-checklist
GET /api/v1/domains/workout/stats
GET /api/v1/domains/{domain}/completed-exercises?date=YYYY-MM-DD
PUT /api/v1/domains/{domain}/completed-exercises
```

These endpoints track:
- completed exercise indices by date
- workout score by completion percentage
- recovery checklist items
- weekly summaries and consistency

## Insights and Progress
Insight routes:
```text
GET   /api/v1/insights/me
GET   /api/v1/insights/me/domain/{domain}
GET   /api/v1/insights/{insight_id}
PATCH /api/v1/insights/{insight_id}/read
```

User and progress routes:
```text
GET   /api/v1/users/me
PATCH /api/v1/users/me
DELETE /api/v1/users/me
GET   /api/v1/users/me/progress/weekly
GET   /api/v1/users/me/progress/graph?period=weekly|monthly|yearly
```

The app tracks two kinds of progress:
- answer completion progress within a domain
- score history over time from AI-generated insights

## Subscription and IAP
Subscription routes:
```text
GET /api/v1/subscriptions/plans
GET /api/v1/subscriptions/me
```

IAP routes:
```text
POST /api/v1/iap/validate-receipt
POST /api/v1/iap/restore-purchases
POST /api/v1/iap/webhooks/apple
POST /api/v1/iap/webhooks/google
GET  /api/v1/iap/products
```

Current status:
- subscription plans are exposed by the backend
- subscription state is checked before protected domain access
- Apple receipt validation exists
- Google receipt validation is only partially implemented
- Apple and Google webhook handling is scaffolded but not fully implemented

## Legal Routes
```text
GET /api/v1/legal/privacy-policy
GET /api/v1/legal/terms-of-service
```

## Environment Variables
Core variables used by the app include:

```env
DATABASE_URI=postgresql+asyncpg://looks_lab:password@localhost:5432/looks_lab
JWT_SECRET=replace-with-a-long-random-secret
JWT_REFRESH_SECRET=replace-with-a-second-long-random-secret
GOOGLE_CLIENT_ID=your-google-client-id
APPLE_CLIENT_ID=your-apple-client-id
GEMINI_API_KEY=your-gemini-api-key
ENV=development
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
TRUSTED_HOSTS=localhost,127.0.0.1
```

Required storage variables (S3-only):
```env
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-private-bucket
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
CLOUDFRONT_DOMAIN=cdn.example.com
APP_URL=http://localhost:8000
```

Useful flags:
```env
RATE_LIMIT_PER_MINUTE=60
BYPASS_SUBSCRIPTION_CHECK=false
ENABLE_SECURITY_HEADERS=true
```

## Local Development
### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Postgres and Redis
Using Docker Compose:
```bash
docker compose up -d db redis
```

### 3. Run migrations
```bash
alembic upgrade head
```

### 4. Seed questions
```bash
python scripts/seed_questions.py
```

### 5. Start the API
```bash
uvicorn app.main:app --reload
```

Docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Docker
Full stack:
```bash
docker compose up --build
```

Services in `docker-compose.yml`:
- `db` for PostgreSQL
- `redis` for Redis
- `app` for FastAPI + Gunicorn

## Database Overview
Main tables:
- `users`
- `refresh_tokens`
- `subscriptions`
- `onboarding_sessions`
- `onboarding_questions`
- `onboarding_answers`
- `domain_questions`
- `domain_answers`
- `images`
- `insights`
- `domain_score_history`
- `workout_completions`
- `daily_recovery`

## Seed Data
Question content comes from:
- `app/data/onboarding_questions.json`
- `app/data/domain_questions.json`

Seeder:
- `scripts/seed_questions.py`

## Known Gaps
As of this README revision, a few parts of the system are scaffolded but still need hardening:
- Google Play receipt validation is incomplete
- Apple and Google billing webhooks need fuller processing
- documentation and ops endpoints should continue to be aligned with the running app

## Quick Summary
If you want the shortest mental model for the backend, it is this:
- onboarding creates context before login
- authentication creates the user
- onboarding session gets linked to that user
- one paid domain is unlocked
- domain answers and images feed Gemini
- Gemini output becomes insights and progress history
- users can revisit insights, upload more images, and track progress over time
