## Looks Lab (Backend)

FastAPI backend for Looks Lab.

### Quickstart (local dev)

- **Create a virtualenv** and install deps:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

- **Configure env**:
  - Copy `env.example` to `.env` and set `JWT_SECRET`
  - Ensure Postgres is running and `DATABASE_URI` points to it

- **Run the API**:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Health check

- `GET /health`

### Migrations (Alembic)

```bash
alembic upgrade head
```

### Tests

Tests expect a Postgres DB. You can override the URL:

```bash
set TEST_DATABASE_URL=postgresql://looks_lab_test:testpassword@localhost:5432/looks_lab_test
pytest -q
```


