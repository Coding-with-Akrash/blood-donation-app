# Free deployment: Render + Neon

This option has **no credit-card requirement** and preserves PostgreSQL. It is for a demo, pilot, or portfolio project—not a live medical service. The Render web service sleeps after 15 inactive minutes and takes about a minute to wake. Do not store real donor or patient data on free services.

## 1. Publish the project

Create a private GitHub repository, then upload this project folder to it. Do not upload `.env`; it contains secrets. GitHub's free private repositories are sufficient.

## 2. Create the PostgreSQL database

1. Sign in to [Neon](https://neon.tech) with Google or GitHub and create a project.
2. In the project dashboard, copy its pooled PostgreSQL connection string. It begins with `postgresql://` and contains a password.
3. Keep it private. It will be entered directly in Render as `DATABASE_URL`.

## 3. Deploy the application

1. Sign in to [Render](https://render.com) with GitHub.
2. Choose **New → Blueprint**, select the repository, and approve the detected `render.yaml`.
3. At the environment-variable screen, enter these values:

   - `DATABASE_URL`: the Neon connection string from step 2.
   - `ADMIN_EMAIL`: the email address for the initial administrator.
   - `ADMIN_PASSWORD`: a unique password of at least 12 characters.

   Render generates `JWT_SECRET`; leave it unchanged.
4. Click **Apply** / **Create Blueprint**. Do not enter a payment method.
5. Wait for the build to complete. Its logs should include `Administrator created` and the health check should pass.
6. Open the `onrender.com` service URL and sign in with the administrator email/password you chose.

## Database and backup limits

Neon Free provides PostgreSQL without a card, but has resource limits. Export a database backup manually on a regular basis with Neon’s SQL/connection tools and store it securely. Render Free has no scheduled jobs, its local files disappear on restarts, and the service sleeps when idle. The source code avoids local database storage, so all application data stays in Neon.

## Troubleshooting

- A `502` on first visit can be the normal Render wake-up delay; wait about one minute and retry.
- If the build fails while connecting to the database, re-copy the entire Neon `DATABASE_URL`, including `sslmode=require`.
- If a user cannot sign in, check the Render logs and confirm `ADMIN_EMAIL` and `ADMIN_PASSWORD` were set before first deployment.
