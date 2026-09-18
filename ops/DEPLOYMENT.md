# Server deployment runbook

## Before deployment

- Use a supported Linux server, a domain name, Docker Engine and the Compose plugin.
- Create a production `.env` from `.env.example`. Generate `JWT_SECRET` with `openssl rand -hex 48`; do not reuse development passwords.
- Set `ALLOWED_ORIGINS` to the exact HTTPS domain. Keep `EXPOSE_API_DOCS=false` in production.
- Restrict network access to ports 80 and 443 only. PostgreSQL is intentionally not published by Compose.

## Deploy

```sh
git clone <your-private-repository-url> blood-donation
cd blood-donation
cp .env.example .env
# Edit .env with production values
docker compose up -d --build
docker compose exec api python -m app.seed
```

Use a host-level reverse proxy such as Caddy, Traefik, or Nginx to terminate TLS and forward HTTPS traffic to the `web` container. The Compose service is deliberately bound only to `127.0.0.1:8080`. With Caddy the essential site block is:

```caddy
blood.example.org {
  reverse_proxy 127.0.0.1:8080
}
```

Verify `/api/health`, sign in, and confirm a test donation cannot be issued twice.

## Backups and recovery

Load `.env` before running backups, then schedule `ops/backup.sh` nightly through the server's scheduler. Copy encrypted backup files off the server and test restoration quarterly in a separate environment. `ops/restore.sh` is intentionally destructive and asks for explicit confirmation.

Example scheduler entry (02:15 UTC):

```cron
15 2 * * * cd /srv/blood-donation && set -a && . ./.env && set +a && ./ops/backup.sh >> /var/log/bloodbank-backup.log 2>&1
```

## Operational checklist

- Enable automatic security updates and monitor container logs.
- Rotate database and JWT secrets according to your organization’s policy.
- Enforce least privilege: only administrators receive the admin role.
- Review audit activity regularly and protect database backups as sensitive health data.
- Obtain clinical/legal review for local donor eligibility rules, retention, consent, blood testing, and compatibility policies before live use.
