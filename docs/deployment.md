# Deployment Guide

## Local Reproducibility

### API

1. Install Python dependencies from `backend/requirements.txt`.
2. Copy `backend/.env.example` to `backend/.env`.
3. Set:
   - `API_KEY`
   - `FMCSA_MOCK_MODE=true` for demos, or `FMCSA_API_KEY` plus `FMCSA_MOCK_MODE=false` for live carrier checks
4. From `backend/`, run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Dashboard

From the repo root, run:

```bash
streamlit run dashboard/app.py
```

## Docker Deployment

From the repo root:

```bash
docker compose up --build
```

Services:

- API on port `8000`
- Dashboard on port `8501`

The compose file binds `backend/data` into both containers so the dashboard sees the same call records the API writes.

## Local Helpers

- Start both local services: `start_local.ps1`
- Stop both local services: `stop_local.ps1`
- Run smoke test after startup: `python backend/scripts/smoke_test.py`

## Cloud Deployment Pattern

### Backend

- Deploy the `backend/Dockerfile` image to your preferred provider.
- Set `PYTHONPATH=/app/backend`.
- Expose port `8000`.
- Configure environment variables from `backend/.env`.
- Mount persistent storage for `backend/data` or switch to a managed database.

### Dashboard

- Deploy the `dashboard/Dockerfile` image separately.
- Expose port `8501`.
- Point it to the same persistent `backend/data/calls.db`, or update it to read through the API.

## HTTPS

For production, terminate HTTPS at the platform edge or reverse proxy:

- AWS ALB / ECS
- Fly.io managed certificates
- Railway managed domain + TLS
- Nginx with Let's Encrypt

For local testing, a self-signed certificate is acceptable if you want to front the API with a local reverse proxy.

## Recommended Production Hardening

- Move from SQLite to Postgres.
- Add structured request logging.
- Add API rate limiting and secret rotation.
- Replace mock FMCSA mode with live verification only in production.
- Add health checks and uptime monitoring.
