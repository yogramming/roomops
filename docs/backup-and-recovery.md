# RoomOps — Backup and Recovery Runbook

## 1. Backup strategy

RoomOps uses PostgreSQL logical backups in custom archive format.

- Database: `roomops`
- Backup utility: `pg_dump`
- Format: Custom (`-Fc`)
- Backup location: `backups/postgres/`
- Naming convention: `roomops-YYYYMMDDTHHMMSSZ.dump`
- Default retention: 7 days

## 2. Create a backup

Run from the repository root:

```bash
./scripts/backup/backup-postgres.sh
```

The script:

1. Executes `pg_dump` inside the PostgreSQL Kubernetes pod.
2. Writes the archive to local storage.
3. Validates the archive using `pg_restore --list`.
4. Publishes the completed backup.
5. Removes expired backup files according to the retention setting.

Override retention:

```bash
RETENTION_DAYS=14 ./scripts/backup/backup-postgres.sh
```

## 3. Inspect a backup

```bash
pg_restore --list backups/postgres/<backup-file>.dump
sha256sum backups/postgres/<backup-file>.dump
```

## 4. Restore into a separate database

Create a test database:

```bash
kubectl --context kind-lab -n roomops exec roomops-postgres-0 -- \
  createdb -U roomops -O roomops roomops_restore_test
```

Restore:

```bash
cat backups/postgres/<backup-file>.dump | \
kubectl --context kind-lab -n roomops exec -i roomops-postgres-0 -- \
  pg_restore -U roomops -d roomops_restore_test \
  --no-owner --exit-on-error
```

## 5. Verify recovery

```sql
SELECT count(*) FROM rooms;
SELECT count(*) FROM reservations;

SELECT conname
FROM pg_constraint
WHERE conname IN (
  'no_overlapping_confirmed_bookings',
  'valid_reservation_date_range',
  'reservations_room_id_fkey'
);

SELECT * FROM alembic_version;
```

Expected baseline from the verified recovery exercise:

- Rooms: 5
- Reservations: 3
- Constraints: 3
- Alembic revision: `5ad9b34a5dff`

## 6. Production recovery precautions

- Confirm the target database and backup before any production restore.
- Preserve the existing PostgreSQL PVC.
- Never restore into the production database without an approved recovery procedure.
- Take a fresh backup before attempting production recovery.
- Validate application health and reservation availability after recovery.

## 7. Recovery test result

On 11 November 2026, a PostgreSQL backup was successfully restored into `roomops_restore_test`.

All five rooms, three reservations, database constraints, and Alembic migration version were verified.

Production data remained untouched.
