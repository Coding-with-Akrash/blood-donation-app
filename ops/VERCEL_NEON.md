# Free demo deployment: Vercel + Neon

This deployment uses **Vercel Hobby** for the web app/API and **Neon Free** for PostgreSQL. Neither requires a credit card to create an account. It is a demonstration system only: do not store actual donor, recipient, or medical information.

## Before deploying

1. Create a free Neon project at [neon.tech](https://neon.tech), using Google or GitHub sign-in.
2. Copy the full connection string from the Neon dashboard. It must include `sslmode=require`.
3. Push this project, including `api/index.py`, `vercel.json`, and `requirements.txt`, to a private GitHub repository. Never commit `.env`.

## Deploy

1. Sign in at [vercel.com](https://vercel.com) with GitHub.
2. Click **Add New → Project**, import the repository, and set the framework preset to **Other**.
3. Before clicking Deploy, add these environment variables for **Production**, **Preview**, and **Development**:

   - `DATABASE_URL` — the Neon connection string
   - `JWT_SECRET` — generate a unique random 64-character value
   - `ADMIN_EMAIL` — the initial administrator’s email address
   - `ADMIN_PASSWORD` — a unique password of at least 12 characters
   - `ALLOWED_ORIGINS` — `https://YOUR-PROJECT.vercel.app`
   - `EXPOSE_API_DOCS` — `false`
   - `SEED_DEMO_DATA` — `false`

4. Click **Deploy**. `vercel.json` builds the React frontend and copies it to `public/`. The FastAPI serverless function initializes on first request, creates the database schema, and seeds the administrator account. Both steps are idempotent.
5. Open the resulting `vercel.app` URL and sign in using the administrator credentials set above.

## Limits

Vercel functions are serverless and may have cold starts. Neon Free has storage and compute limits. There is no scheduled backup job on this free path: create regular manual database exports from Neon. Use the Docker/Oracle or a paid hosting plan before handling real health information.
