#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: ./ops/restore.sh backups/bloodbank-YYYYMMDDTHHMMSSZ.dump" >&2
  exit 2
fi
printf 'This replaces data in %s. Type RESTORE to continue: ' "$POSTGRES_DB"
read answer
[ "$answer" = "RESTORE" ] || { echo "Cancelled."; exit 1; }
docker compose exec -T db pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner < "$1"
