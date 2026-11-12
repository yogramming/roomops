# RoomOps — Rollback and Recovery Runbook

## 1. Purpose

This runbook describes how to recover RoomOps after a failed application
deployment, configuration change, infrastructure upgrade, or database incident.

The deployment uses:
- Kubernetes (Kind cluster: `lab`, context: `kind-lab`)
- Helm for RoomOps and observability releases
- ArgoCD for GitOps management of Gateway resources
- PostgreSQL StatefulSet with persistent storage
- PostgreSQL logical backups in custom archive format

**Important:** Application rollback and database rollback are separate operations.
Reverting an application release does not automatically reverse database
migrations or restore database contents.

## 2. Recovery principles

1. Identify the affected component before taking action.
2. Preserve the PostgreSQL PVC and existing database contents.
3. Prefer reverting to a previously verified healthy release.
4. Check database compatibility before reverting application code.
5. Verify health, readiness, logs, and API behavior after recovery.
6. Record the incident, action taken, and verification results.

Never delete the PostgreSQL PVC or use `helm uninstall` as a recovery shortcut.

## 3. Application rollback using Helm

RoomOps API is deployed through the Helm release `roomops` in namespace
`roomops`.

### 3.1 Inspect release history

```bash
helm history roomops -n roomops
```

Inspect a candidate revision before using it:

```bash
helm get values roomops -n roomops --revision <REVISION>
helm get manifest roomops -n roomops --revision <REVISION>
```

Check that the candidate revision:
- Enables the API (`api.enabled: true`).
- Uses the intended application image.
- Has compatible configuration and database expectations.
- Does not unintentionally change PostgreSQL storage or credentials.

**Known project-specific warning:** Revision 4 has `api.enabled: false`.
Do not use revision 4 as an API rollback target. Revision 5 is the known
deployed configuration at the time this runbook was written.

### 3.2 Roll back to a verified revision

Replace `<REVISION>` with the revision you inspected and verified:

```bash
helm rollback roomops <REVISION> \
  -n roomops \
  --wait \
  --timeout 5m
```

Check the release and workloads:

```bash
helm status roomops -n roomops
kubectl -n roomops get deployments,pods,services
kubectl -n roomops rollout status deployment/roomops-api --timeout=180s
```

Verify the API:

```bash
kubectl -n roomops port-forward svc/roomops-api 18000:8000
```

In another terminal:

```bash
curl -fsS http://127.0.0.1:18000/health
curl -fsS http://127.0.0.1:18000/ready
```

Stop the port-forward with `Ctrl+C`.

Also verify a representative availability request and reservation lookup
using the API's documented endpoints.

## 4. Helm rollback for observability components

Inspect release history before reverting an observability component:

```bash
helm history roomops-grafana -n monitoring
helm history roomops-loki -n monitoring
helm history roomops-alloy -n monitoring
helm history roomops-prometheus -n monitoring
```

Inspect the selected revision and its values before rollback:

```bash
helm get values <RELEASE> -n monitoring --revision <REVISION>
```

Roll back only the affected release:

```bash
helm rollback <RELEASE> <REVISION> \
  -n monitoring \
  --wait \
  --timeout 5m
```

Verify the release and its pods:

```bash
helm status <RELEASE> -n monitoring
kubectl get pods -n monitoring
```

Use the actual release names shown by `helm list -n monitoring`.
Do not roll back unrelated observability components.

## 5. GitOps rollback for Gateway resources

ArgoCD manages the Gateway resources in this project. It does not manage
the RoomOps API Helm release.

If a committed Gateway configuration change causes a problem:

1. Identify the commit that introduced the bad configuration.
2. Revert that commit on the Git branch monitored by ArgoCD.
3. Push the revert.
4. Allow ArgoCD to synchronize the corrected configuration.

Example:

```bash
git log --oneline -10
git revert <BAD_COMMIT>
git push origin main
```

Check ArgoCD application status:

```bash
kubectl get applications -n argocd
kubectl describe application <APPLICATION_NAME> -n argocd
```

Verify the Gateway and route:

```bash
kubectl get gateway,httproute -A
```

Do not manually edit ArgoCD-managed resources as the permanent fix.
Correct the Git source instead.

## 6. Application restart and recovery

For an unhealthy API deployment, inspect the workload first:

```bash
kubectl -n roomops get pods
kubectl -n roomops describe deployment roomops-api
kubectl -n roomops logs deployment/roomops-api --tail=100
```

If the application is stuck or needs a restart:

```bash
kubectl -n roomops rollout restart deployment/roomops-api
kubectl -n roomops rollout status deployment/roomops-api --timeout=180s
```

Verify:

```bash
kubectl -n roomops get pods
kubectl -n roomops get deployment roomops-api
```

Then check `/health`, `/ready`, and a representative API request.

For PostgreSQL incidents, inspect before taking action:

```bash
kubectl -n roomops get statefulset,pods,pvc
kubectl -n roomops describe pod roomops-postgres-0
kubectl -n roomops logs roomops-postgres-0 --tail=100
```

Do not delete the PostgreSQL PVC. Database restarts or recovery operations
should be performed only after assessing database health and data safety.

## 7. Database backup and restore

Use the separate backup runbook:

[`backup-and-recovery.md`](backup-and-recovery.md)

Create and validate a backup before any approved production recovery:

```bash
./scripts/backup/backup-postgres.sh
pg_restore --list backups/postgres/<BACKUP_FILE>.dump
sha256sum backups/postgres/<BACKUP_FILE>.dump
```

The tested restore procedure restores into a separate database:

```bash
kubectl --context kind-lab -n roomops exec roomops-postgres-0 -- \
  createdb -U roomops -O roomops roomops_restore_test
```

```bash
cat backups/postgres/<BACKUP_FILE>.dump | \
kubectl --context kind-lab -n roomops exec -i roomops-postgres-0 -- \
  pg_restore -U roomops -d roomops_restore_test \
  --no-owner --exit-on-error
```

Verify the restored database:

```bash
kubectl --context kind-lab -n roomops exec roomops-postgres-0 -- \
  psql -U roomops -d roomops_restore_test -c \
  "SELECT count(*) FROM rooms;"

kubectl --context kind-lab -n roomops exec roomops-postgres-0 -- \
  psql -U roomops -d roomops_restore_test -c \
  "SELECT count(*) FROM reservations;"

kubectl --context kind-lab -n roomops exec roomops-postgres-0 -- \
  psql -U roomops -d roomops_restore_test -c \
  "SELECT * FROM alembic_version;"
```

The verified recovery exercise on 11 November 2026 restored:
- 5 rooms
- 3 reservations
- All three expected database constraints
- Alembic revision `5ad9b34a5dff`

The production `roomops` database was not modified.

**Production restore warning:** The commands above are a test restore into a
separate database, not a production restore procedure. A production restore
requires an approved outage/recovery plan, a verified backup, a fresh
pre-recovery backup, and explicit validation of the target database.
Do not restore over the live database by copying these test commands.

## 8. Database migration rollback

Application rollback does not reverse Alembic migrations.

Before considering a migration downgrade:

1. Identify the current and target migration revisions.
2. Review the migration's downgrade operation.
3. Confirm that the older application version is compatible with the
   resulting schema.
4. Take and validate a database backup.
5. Obtain approval before changing the live database.

Inspect migration state:

```bash
flask db current
flask db history
```

A downgrade is intentionally not presented as a routine recovery command:
the project's migration downgrade behavior has not been demonstrated as a
safe production recovery procedure.

When a downgrade is unsafe or data may be lost, use the approved database
recovery plan instead.

## 9. Post-recovery verification checklist

- [ ] Helm release reports the expected deployed revision.
- [ ] RoomOps API Deployment is available.
- [ ] API pods are Running and Ready.
- [ ] `/health` responds successfully.
- [ ] `/ready` responds successfully.
- [ ] Availability query returns an expected response.
- [ ] Reservation creation and retrieval work.
- [ ] PostgreSQL pod and PVC remain healthy.
- [ ] Application logs show no new critical errors.
- [ ] Prometheus metrics and application logs are available.
- [ ] Recovery actions and evidence are recorded.

## 10. Current verification status

| Capability | Status |
|---|---|
| PostgreSQL backup creation | Implemented |
| Backup archive validation | Implemented |
| Restore into separate database | Tested successfully |
| API deployment through Helm | Implemented |
| Helm application rollback procedure | Documented; live rollback test pending |
| Observability Helm rollback procedure | Documented; rollback test pending |
| ArgoCD Gateway Git revert procedure | Documented; recovery test pending |
| API restart procedure | Documented; recovery demonstration pending |
| Production database restore | Not tested |
| Alembic downgrade recovery | Not tested |

This runbook describes the available recovery mechanisms without claiming
that untested recovery operations have been verified.

## 11. Envoy Gateway controller rollback

The Envoy Gateway controller uses Helm release `eg` in namespace
`envoy-gateway-system`. This is separate from Gateway resources managed
by ArgoCD.

Inspect release history and the candidate revision:

```bash
helm history eg -n envoy-gateway-system
helm get values eg -n envoy-gateway-system --revision REVISION_NUMBER
```

After verifying the candidate revision, replace `REVISION_NUMBER` with
its actual numeric value:

```bash
helm rollback eg REVISION_NUMBER -n envoy-gateway-system --wait --timeout 5m
```

Verify the controller and Gateway resources:

```bash
helm status eg -n envoy-gateway-system
kubectl get pods -n envoy-gateway-system
kubectl get gateway,httproute -A
```

Do not confuse controller rollback with reverting Gateway configuration
through ArgoCD.
