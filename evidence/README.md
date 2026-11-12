# RoomOps — Assessment Evidence

This directory contains evidence collected from the RoomOps CI/CD pipeline,
automated tests, Kubernetes deployment, GitOps workflow, observability stack,
and database recovery exercises.

## 1. CI/CD — `ci/`

- `jenkins-success.png` — Successful Jenkins pipeline build.
- `jenkins-console.txt` — Jenkins build console output.
- `image-metadata.txt` — Container image metadata and digest.
- `trivy-scan.txt` — Container vulnerability scan results.

## 2. Automated Tests — `tests/`

- `concurrency-test.txt` — PostgreSQL concurrent reservation tests,
  including overlapping and non-overlapping reservations.
- `api-test-results.txt` — Complete API test suite results.

## 3. Kubernetes Deployment — `deployment/`

- `kubernetes-status.txt` — Kubernetes nodes, workloads, services,
  and persistent volume claims.
- `https-health.txt` — HTTPS health and readiness endpoint responses.
- `application-logs.txt` — RoomOps API application logs.

## 4. GitOps — `gitops/`

- `argocd-application.png` — ArgoCD application status and managed resources.

## 5. Observability — `observability/`

- `grafana-dashboard.png` — RoomOps Grafana monitoring dashboard.
- `loki-application-logs.png` — Application logs queried through Loki.

## 6. Backup and Recovery — `recovery/`

- `backup-creation.txt` — PostgreSQL backup inventory and archive validation.
- `backup-restore.txt` — Restore verification using a separate database.
- `rollback-procedure.md` — Documented application, infrastructure,
  GitOps, and database recovery procedures.

## 7. Additional Kubernetes Evidence — `kubernetes/`

Contains supporting Kubernetes manifests, deployment details,
database constraints, migration records, certificates, and cluster status.

## Evidence Notes

- Evidence reflects the state of the project when each item was collected.
- The PostgreSQL restore exercise used a separate test database;
  the production database was not modified.
- Documented rollback procedures are not represented as successfully
  tested unless corresponding execution evidence is available.
- Container vulnerability results and image metadata correspond to
  the image identified in the CI evidence.
