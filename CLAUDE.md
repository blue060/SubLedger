# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SubLedger is a self-hosted Chinese-language subscription management tool (similar to Wallos). The entire UI is in Chinese — buttons, prompts, error messages, everything.

## Tech Stack

- **Backend**: Python 3.12 + FastAPI + SQLAlchemy + SQLite
- **Frontend**: Vue 3 + TypeScript + Element Plus + ECharts
- **Deployment**: Docker + docker-compose

## Commands

```bash
# Backend
cd backend
pip install -r requirements.txt
ADMIN_PASSWORD=your-password uvicorn app.main:app --reload --port 8080

# Backend tests
cd backend
ADMIN_PASSWORD=testpassword pytest tests/ -v

# Frontend dev
cd frontend
npm install
npm run dev

# Frontend build
cd frontend
npm run build

# Docker
docker compose up -d
```

## Architecture

- REST API at `/api/*`, backend serves Vue build output at root path
- Single-user auth: JWT in HttpOnly cookie (`subledger_token`) + CSRF double-submit (`subledger_csrf` cookie vs `X-CSRF-Token` header)
- `backend/app/main.py`: app factory with lifespan (DB seed, APScheduler start/stop), middleware stack, router mounting
- `backend/app/models.py`: all SQLAlchemy models in one file (User, Category, Subscription, Notification, AppSettings)
- `backend/app/services/`: business logic (billing.py for next-payment-date calc, exchange_rate.py for currency conversion, notifier.py for email/push, scheduler.py for daily check job)
- `frontend/src/locales/zh-CN.ts`: all Chinese UI strings — single source of truth
- `frontend/src/composables/useApi.ts`: axios instance with CSRF header injection and 401 redirect

## Key Patterns

- `next_payment_date` is pre-computed on create/update (via `billing.calculate_next_payment_date`) and stored, not computed on read
- Exchange rates cached in `AppSettings.exchange_rate_cache` (JSON, 24h TTL), falls back to stale cache on API failure
- APScheduler daily midnight job checks upcoming subscriptions, creates Notification rows, sends via configured channels
- Test app in conftest.py skips lifespan to avoid side effects; TestClient cookie persistence is a known limitation

## Constraints

- All UI text must be in Chinese
- Single-user only — no multi-user registration
- `ADMIN_PASSWORD` env var is required at startup
- CSRF check on all mutating requests (excluding login and health)