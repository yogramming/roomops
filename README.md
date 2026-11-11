# RoomOps

A reproducibly buildable, deployable, observable, and recoverable Room
Availability and Reservation Service.

## Project scope

RoomOps provides:
- Room availability queries by date range and room type.
- Reservation creation with unique references and date validation.
- Protection against overlapping confirmed reservations, including
  concurrent requests.
- PostgreSQL persistence.
- Health, readiness, and metrics endpoints.

## Technology stack

Flask, PostgreSQL, SQLAlchemy, Alembic, Docker, Kubernetes, Helm,
Jenkins, ArgoCD, Prometheus, Grafana, Loki, and Grafana Alloy.

## Documentation

- [Backup and Recovery](docs/backup-and-recovery.md)
- [Rollback and Recovery](docs/rollback-and-recovery.md)

## Repository structure

- `app/` — API application and domain logic
- `tests/` — automated API and business-rule tests
- `migrations/` — database migrations
- `scripts/` — seed and operational scripts
- `helm/` — Kubernetes application chart
- `observability/` — Prometheus, Grafana, Loki, and Alloy configuration
- `docs/` — operational runbooks and project documentation
- `evidence/` — assessment and deployment evidence

## Local development

Create and activate a virtual environment, install dependencies, configure
environment variables, and start the application using the documented
Compose setup.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

See the project configuration and operational documentation for deployment,
database, backup, and recovery procedures.
