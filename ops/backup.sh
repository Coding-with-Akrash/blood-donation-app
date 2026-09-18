#!/usr/bin/env sh
set -eu

# Run from the server folder that contains docker-compose.yml and .env.
# Retention defaults to 14 days; set BACKUP_DIR and RETENTION_DAYS if desired.
backup_dir="${BACKUP_DIR:-./backups}"
retention_days="${RETENTION_DAYS:-14}"
mkdir -p "$backup_dir"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom > "$backup_dir/bloodbank-$timestamp.dump"
find "$backup_dir" -type f -name 'bloodbank-*.dump' -mtime +"$retention_days" -delete
echo "Created $backup_dir/bloodbank-$timestamp.dump"
