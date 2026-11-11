#!/usr/bin/env bash
set -Eeuo pipefail

NAMESPACE="${NAMESPACE:-roomops}"
POD="${POD:-roomops-postgres-0}"
CONTEXT="${CONTEXT:-kind-lab}"
BACKUP_DIR="${BACKUP_DIR:-backups/postgres}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_FILE="${BACKUP_DIR}/roomops-${TIMESTAMP}.dump"

mkdir -p "$BACKUP_DIR"

echo "Starting PostgreSQL backup..."
echo "Namespace: $NAMESPACE"
echo "Pod: $POD"
echo "Output: $BACKUP_FILE"

kubectl --context "$CONTEXT" -n "$NAMESPACE" exec "$POD" -- \
  pg_dump -U roomops -d roomops -Fc \
  > "$BACKUP_FILE"

if [[ ! -s "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file is empty."
    rm -f "$BACKUP_FILE"
    exit 1
fi

echo "Validating backup archive..."
pg_restore --list "$BACKUP_FILE" > /dev/null

echo "Backup completed successfully."
echo "File: $BACKUP_FILE"
echo "Size: $(du -h "$BACKUP_FILE" | cut -f1)"
