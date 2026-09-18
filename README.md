# Blood Donation Department

A production-oriented blood bank management system with a React dashboard, FastAPI API, PostgreSQL, role-based access, immutable audit events, Docker deployment, backups, and operational documentation. Ready for Vercel + Neon demonstration deployments.

## Architecture

```
Browser -> Nginx (React SPA + /api proxy) -> FastAPI -> PostgreSQL
                                           -> SMTP provider (optional)
```

Roles: **donor** can manage their profile and see their donation history; **staff** manages donors, donations, inventory, and requests; **admin** additionally manages users and views audit activity.

Core API workflows include donor self-registration, eligibility checks, donation screening/deferral, component-unit creation, expiry management, recipient requests, atomic unit issuance, notifications, dashboard/report summaries, search/filtering, and administrator audit/user endpoints.

## Repository layout

```
backend/       FastAPI application, migrations, seed data and tests
frontend/      React + TypeScript dashboard
nginx/         production reverse proxy and SPA configuration
ops/           backup and server deployment helpers
docker-compose.yml
```

## Quick start

1. Copy `.env.example` to `.env` and replace every secret.
2. Run `docker compose up -d --build`.
3. Run migrations: `docker compose exec api alembic upgrade head`.
4. Seed the first administrator: `docker compose exec api python -m app.seed`.
5. Visit `http://localhost:8080` and sign in with `ADMIN_EMAIL` / `ADMIN_PASSWORD`.

The API documentation is at `/api/docs` when `EXPOSE_API_DOCS=true`.

For a local UI demonstration only, set `SEED_DEMO_DATA=true` before running the seed command. It creates clearly labeled anonymized fixtures; never enable it in a clinical deployment.

## Vercel + Neon deployment

This project is ready for a no-credit-card demonstration deployment on Vercel with Neon PostgreSQL.

1. Create a free Neon database at [neon.tech](https://neon.tech) and copy the pooled connection string. It must include `sslmode=require`.
2. Push this repository to a private GitHub repository. Do not commit `.env`.
3. In [Vercel](https://vercel.com), import the repository and set the framework to **Other**.
4. Add the environment variables from `.env.example`, especially:
   - `DATABASE_URL` — the Neon connection string
   - `JWT_SECRET` — a unique random 64-character value
   - `ADMIN_EMAIL` — the initial administrator email
   - `ADMIN_PASSWORD` — a unique password of at least 12 characters
   - `ALLOWED_ORIGINS` — `https://YOUR-PROJECT.vercel.app`
   - `EXPOSE_API_DOCS` — `false`
   - `SEED_DEMO_DATA` — `false`
5. Vercel automatically builds the frontend and deploys the FastAPI serverless function. The first initialization creates the database schema and administrator account.
6. Open the deployed URL and sign in with the administrator credentials.

See [ops/VERCEL_NEON.md](ops/VERCEL_NEON.md) for detailed steps and limits.

## Development

With PostgreSQL available at the `DATABASE_URL` configured in `.env`, run the API from `backend/` with `uvicorn app.main:app --reload --port 8000`. From `frontend/`, run `npm install` once and `npm run dev`; Vite proxies API calls to the local FastAPI service.

Read [ops/DEPLOYMENT.md](ops/DEPLOYMENT.md) before putting the service on the public internet.

For a no-credit-card demonstration deployment using Vercel Functions and Neon PostgreSQL, see `ops/VERCEL_NEON.md`.
