# RoomOps — Room Availability & Reservation Service

A reproducibly buildable, deployable, observable, and recoverable room availability and reservation service, built with a focus on **DevOps engineering, Kubernetes operations, CI/CD automation, reliability, and infrastructure management**.

RoomOps provides REST APIs for checking room availability and managing reservations. The project demonstrates the complete application delivery lifecycle, from source code and automated testing to containerization, Kubernetes deployment, monitoring, and database recovery.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Key Features](#key-features)
- [API Reference](#api-reference)
- [Database Design](#database-design)
- [Getting Started](#getting-started)
- [Docker and Docker Compose](#docker-and-docker-compose)
- [Kubernetes Deployment](#kubernetes-deployment)
- [CI/CD Pipeline](#cicd-pipeline)
- [GitOps with ArgoCD](#gitops-with-argocd)
- [Monitoring and Observability](#monitoring-and-observability)
- [Security](#security)
- [Testing](#testing)
- [Backup and Recovery](#backup-and-recovery)
- [Repository Structure](#repository-structure)
- [Evidence and Documentation](#evidence-and-documentation)
- [Current Limitations](#current-limitations)

---

## Overview

RoomOps was developed as a deployable backend service with an emphasis on operational reliability rather than application development alone.

The project addresses several important engineering concerns:

- Reliable room availability and reservation management.
- Prevention of conflicting reservations, including concurrent requests.
- Persistent PostgreSQL storage and database migrations.
- Reproducible container builds.
- Automated CI pipelines with testing and vulnerability scanning.
- Kubernetes-based application deployment.
- GitOps-based management of Gateway resources.
- Metrics collection, dashboards, and centralized application logging.
- Database backup, restoration, and rollback documentation.

## Architecture

The system separates application services, persistent storage, external traffic management, CI/CD, and observability.

```mermaid
flowchart TB
    U["Client"] --> GW["Envoy Gateway"]
    GW --> TLS["HTTPS / TLS Termination"]
    TLS --> API["RoomOps Flask API"]
    API --> DB[("PostgreSQL")]

    subgraph Kubernetes["Kubernetes Cluster"]
        GW
        TLS
        API
        DB
        API --> MET["Prometheus Metrics"]
        MET --> PROM["Prometheus"]
        PROM --> GRAF["Grafana"]
        API --> LOG["Container Logs"]
        LOG --> ALLOY["Grafana Alloy"]
        ALLOY --> LOKI["Loki"]
        GRAF --> LOKI
    end

    subgraph Delivery["CI/CD and GitOps"]
        GH["GitHub Repository"]
        J["Jenkins CI"]
        TR["Trivy Scan"]
        DH["Docker Hub"]
        ARGO["ArgoCD"]
        GH --> J
        J --> TR
        TR --> DH
        GH --> ARGO
        ARGO --> GW
    end
```

### Application request flow

1. Clients access the service through the Envoy Gateway.
2. HTTPS traffic is terminated using a Kubernetes TLS Secret.
3. The HTTPRoute forwards requests to the RoomOps API service.
4. The Flask application validates requests and executes business logic.
5. PostgreSQL persists room and reservation information.
6. Prometheus collects application metrics.
7. Grafana Alloy collects Kubernetes container logs and forwards them to Loki.
8. Grafana provides dashboards using Prometheus and Loki as data sources.

### Delivery flow

1. Developers push changes to GitHub.
2. Jenkins checks out the source and creates an isolated Python environment.
3. Ruff performs static linting.
4. Jenkins starts an ephemeral PostgreSQL instance.
5. Alembic applies migrations and pytest executes the test suite.
6. Docker builds an image tagged with the Git commit SHA.
7. Trivy scans the image for HIGH and CRITICAL vulnerabilities.
8. Successful images are published to Docker Hub using versioned and `latest` tags.

---

## Technology Stack

| Category           | Technologies                          |
| ------------------ | ------------------------------------- |
| Backend            | Python, Flask                         |
| Database           | PostgreSQL 17                         |
| ORM                | SQLAlchemy, Flask-SQLAlchemy          |
| Migrations         | Alembic, Flask-Migrate                |
| Application Server | Gunicorn                              |
| Containerization   | Docker, Docker Compose                |
| Orchestration      | Kubernetes (Kind)                     |
| Package Management | Helm                                  |
| CI/CD              | Jenkins                               |
| Container Registry | Docker Hub                            |
| Security Scanning  | Trivy                                 |
| GitOps             | ArgoCD                                |
| Gateway / Ingress  | Kubernetes Gateway API, Envoy Gateway |
| Metrics            | Prometheus, prometheus-client         |
| Dashboards         | Grafana                               |
| Log Aggregation    | Grafana Loki                          |
| Log Collection     | Grafana Alloy                         |
| Testing            | pytest, pytest-cov                    |
| Code Quality       | Ruff                                  |

---

## Key Features

### Room availability

- Query available rooms using check-in and check-out dates.
- Filter rooms by room type.
- Exclude rooms with overlapping confirmed reservations.
- Return available room numbers and types.

### Reservation management

- Create reservations with unique references.
- Retrieve reservations using their reference.
- Validate required fields and date formats.
- Reject invalid reservation date ranges.
- Return appropriate HTTP status codes for validation and reservation conflicts.

### Database-level concurrency protection

Reservation conflicts are prevented using a PostgreSQL GiST exclusion constraint rather than relying exclusively on application-level checks.

The constraint combines:

- Room ID equality.
- PostgreSQL date-range overlap detection.
- A condition applying only to confirmed reservations.

This protects the database against overlapping confirmed reservations for the same room, including concurrent requests.

### Operational endpoints

- Liveness endpoint.
- Database readiness endpoint.
- Prometheus metrics endpoint.
- Structured application logging.

---

## API Reference

The API uses JSON for request and response bodies.

| Method | Endpoint                           | Description             |
| ------ | ---------------------------------- | ----------------------- |
| GET    | `/health`                          | Application health      |
| GET    | `/ready`                           | Database readiness      |
| GET    | `/metrics`                         | Prometheus metrics      |
| GET    | `/api/v1/rooms/availability`       | Check room availability |
| POST   | `/api/v1/reservations`             | Create a reservation    |
| GET    | `/api/v1/reservations/<reference>` | Retrieve a reservation  |

### 1. Health check

```http
GET /health
```

Example response:

```json
{
  "status": "healthy",
  "service": "roomops"
}
```

### 2. Readiness check

```http
GET /ready
```

Checks database connectivity before reporting the application as ready.

Example response:

```json
{
  "status": "ready",
  "database": "connected"
}
```

### 3. Check room availability

```http
GET /api/v1/rooms/availability?check_in=2030-05-10&check_out=2030-05-13&room_type=deluxe
```

Parameters:

| Parameter   | Required | Description                   |
| ----------- | -------- | ----------------------------- |
| `check_in`  | Yes      | Check-in date (`YYYY-MM-DD`)  |
| `check_out` | Yes      | Check-out date (`YYYY-MM-DD`) |
| `room_type` | No       | Room type filter              |

Example response:

```json
{
  "check_in": "2030-05-10",
  "check_out": "2030-05-13",
  "room_type": "deluxe",
  "count": 1,
  "rooms": [
    {
      "room_number": "102",
      "room_type": "deluxe"
    }
  ]
}
```

### 4. Create a reservation

```http
POST /api/v1/reservations
Content-Type: application/json
```

Request body:

```json
{
  "room_number": "102",
  "check_in": "2030-05-10",
  "check_out": "2030-05-13"
}
```

Example response:

```json
{
  "message": "Reservation created successfully",
  "reservation": {
    "reference": "RSV-XXXXXXXXXXXX",
    "room_number": "102",
    "check_in": "2030-05-10",
    "check_out": "2030-05-13",
    "status": "CONFIRMED"
  }
}
```

A successful creation returns HTTP `201`.

### 5. Retrieve a reservation

```http
GET /api/v1/reservations/RSV-XXXXXXXXXXXX
```

Returns reservation details for the supplied reference.

### HTTP status codes

| Status | Meaning                                  |
| ------ | ---------------------------------------- |
| `200`  | Successful request                       |
| `201`  | Reservation created                      |
| `400`  | Invalid request or date validation error |
| `404`  | Room or reservation not found            |
| `409`  | Reservation conflict or integrity error  |
| `503`  | Database readiness failure               |
| `500`  | Database processing error                |

---

## Database Design

RoomOps uses PostgreSQL as its persistent relational database.

### Rooms table

| Column        | Description                               |
| ------------- | ----------------------------------------- |
| `id`          | Primary key                               |
| `room_number` | Unique room identifier                    |
| `room_type`   | Room category                             |
| `is_active`   | Whether the room is available for booking |

### Reservations table

| Column       | Description                    |
| ------------ | ------------------------------ |
| `id`         | UUID primary key               |
| `reference`  | Unique reservation reference   |
| `room_id`    | Foreign key referencing rooms  |
| `check_in`   | Reservation start date         |
| `check_out`  | Reservation end date           |
| `status`     | CONFIRMED or CANCELLED         |
| `created_at` | Reservation creation timestamp |

### Database constraints

The database enforces:

- Unique room numbers.
- Unique reservation references.
- Valid reservation date ranges.
- Foreign-key relationships between rooms and reservations.
- No overlapping confirmed reservations for the same room.

The overlap protection is implemented using PostgreSQL's `btree_gist` extension and a GiST exclusion constraint:

```sql
EXCLUDE USING GIST (
    room_id WITH =,
    daterange(check_in, check_out, '[)') WITH &&
)
WHERE (status = 'CONFIRMED')
```

The half-open date range `[)` allows back-to-back reservations. For example, a reservation ending on May 13 does not conflict with another beginning on May 13.

### Database migrations

Alembic manages schema changes.

```bash
flask --app 'app:create_app()' db upgrade
```

Current migration history:

- `82cf43dda221` — Create rooms and reservations tables.
- `5ad9b34a5dff` — Add reservation overlap constraint.

---

## Getting Started

### Prerequisites

- Python 3.14
- PostgreSQL 17
- Docker and Docker Compose (for containerized execution)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/yogramming/roomops.git
cd roomops
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements-dev.txt
```

### 4. Configure environment variables

Create a local environment file:

```bash
cp .env.example .env
```

Configure the database credentials and application secret.

Example:

```env
FLASK_APP=run.py
FLASK_DEBUG=0

APP_ENV=production
LOG_LEVEL=INFO

SECRET_KEY=replace_with_a_long_random_secret

POSTGRES_DB=roomops
POSTGRES_USER=roomops
POSTGRES_PASSWORD=replace_with_a_strong_local_password

DATABASE_URL=postgresql+psycopg://roomops:replace_with_a_strong_local_password@localhost:5433/roomops
```

Never commit real credentials or production secrets.

### 5. Start PostgreSQL

Start the database using Docker Compose:

```bash
docker compose up -d postgres
```

Check its status:

```bash
docker compose ps
```

### 6. Apply migrations

```bash
flask --app 'app:create_app()' db upgrade
```

### 7. Seed the database

```bash
python -m scripts.seed
```

The seed script creates five sample rooms and one sample reservation. It is designed to avoid duplicating existing seed records.

### 8. Start the application

```bash
python run.py
```

The application is available at:

```text
http://localhost:5000
```

Check the health endpoint:

```bash
curl http://localhost:5000/health
```

Check database readiness:

```bash
curl http://localhost:5000/ready
```

---

## Docker and Docker Compose

RoomOps uses a multi-stage Dockerfile to separate dependency installation from the runtime image.

### Docker image characteristics

- Python 3.14 slim Bookworm base image.
- Multi-stage build.
- Runtime dependencies installed separately.
- Non-root application user (`10001:10001`).
- Gunicorn application server.
- Python bytecode generation disabled.
- Unbuffered Python output.
- Prometheus multiprocess directory configured.

### Build the image

```bash
docker build -t roomops:local .
```

### Start the application stack

Ensure `.env` is configured, then run:

```bash
docker compose up --build -d
```

The Compose configuration provides:

- PostgreSQL service.
- RoomOps API service.
- Persistent PostgreSQL volume.
- PostgreSQL health check.
- Application readiness health check.
- Startup dependency on healthy PostgreSQL.
- Localhost-only host port bindings.

### Inspect running services

```bash
docker compose ps
```

### View application logs

```bash
docker compose logs -f app
```

### Stop services

```bash
docker compose down
```

The named database volume is retained when using this command. Avoid `docker compose down -v` unless intentionally deleting local database storage.

Database migrations and seeding are separate initialization steps; starting Compose does not automatically execute them.

---

## Kubernetes Deployment

RoomOps uses Kubernetes for application orchestration and Helm for repeatable application deployment.

The tested environment uses a multi-node Kind cluster.

### Kubernetes resources

| Resource              | Purpose                              |
| --------------------- | ------------------------------------ |
| Deployment            | RoomOps API                          |
| Service               | Internal API access                  |
| StatefulSet           | PostgreSQL                           |
| PersistentVolumeClaim | Database persistence                 |
| Secret                | Application and database credentials |
| GatewayClass          | Envoy Gateway controller integration |
| Gateway               | HTTPS entry point                    |
| HTTPRoute             | Application traffic routing          |

### Helm chart

The application chart is located at:

```text
helm/roomops/
```

It includes:

- API Deployment and Service.
- PostgreSQL StatefulSet and Service.
- Configurable image repository and tag.
- Resource requests and limits.
- Readiness and liveness probes.
- Existing Kubernetes Secret integration.
- Optional database migration job.

The chart uses an existing Secret named `roomops-secrets` by default. Its required keys are:

- `secret-key`
- `postgres-password`
- `database-url`

Create the Secret before installing the chart, using values appropriate for your environment.

### Deploy using Helm

```bash
helm upgrade --install roomops ./helm/roomops \
  --namespace roomops \
  --create-namespace
```

Inspect the release:

```bash
helm status roomops -n roomops
```

Check workloads:

```bash
kubectl get pods -n roomops
kubectl get services -n roomops
kubectl get pvc -n roomops
```

### Kubernetes health checks

The API Deployment uses:

- Liveness probe: `/health`
- Readiness probe: `/ready`

PostgreSQL uses `pg_isready` for readiness and liveness checks.

### Persistent storage

PostgreSQL is deployed as a StatefulSet with a persistent volume claim.

The configured storage request is `2Gi`, using the `standard` storage class.

The database is not treated as disposable application storage. Removing or reinstalling application releases must not be confused with database recovery.

---

## CI/CD Pipeline

Jenkins automates the RoomOps continuous integration and container publishing workflow.

The pipeline is defined in:

```text
Jenkinsfile
```

### Pipeline stages

| Stage                       | Description                                    |
| --------------------------- | ---------------------------------------------- |
| Checkout                    | Retrieves source code from SCM                 |
| Setup Python                | Creates an isolated virtual environment        |
| Lint                        | Runs Ruff                                      |
| Start PostgreSQL            | Starts an ephemeral PostgreSQL 17 container    |
| Database Migrations & Tests | Applies Alembic migrations and runs pytest     |
| Build Docker Image          | Builds an image tagged with the Git commit SHA |
| Trivy Security Scan         | Scans for HIGH and CRITICAL vulnerabilities    |
| Publish to Docker Hub       | Publishes versioned and `latest` images        |

### Image tagging

Images are tagged using the Git commit SHA:

```text
yogramming/roomops:<commit-sha>
yogramming/roomops:latest
```

Commit-specific tags provide traceability between source revisions, CI builds, and container artifacts.

### CI reliability measures

- Isolated Python environment per build.
- Ephemeral PostgreSQL test database.
- Database readiness polling.
- Automatic migration execution.
- Automated linting and testing.
- Build failure on configured HIGH/CRITICAL Trivy findings.
- Jenkins credential integration for Docker Hub authentication.
- Cleanup of temporary database containers and CI environments.

### Build evidence

See:

```text
evidence/ci/
```

This directory contains the successful Jenkins build screenshot, console output, image metadata, and Trivy scan output.

---

## GitOps with ArgoCD

ArgoCD is used to manage the Kubernetes Gateway resources declaratively.

The application definition is located at:

```text
argocd/roomops-gateway.yaml
```

### GitOps configuration

- Repository: `https://github.com/yogramming/roomops.git`
- Branch: `main`
- Manifest path: `k8s/gateway`
- Destination namespace: `roomops`
- Automated synchronization enabled.
- Self-healing enabled.
- Pruning disabled.

### Managed resources

ArgoCD manages:

- GatewayClass
- Gateway
- HTTPRoute

**Deployment boundary:** The RoomOps application is deployed through Helm. ArgoCD manages the Gateway configuration, not the application Helm release or Envoy Gateway controller installation.

### Traffic management

Envoy Gateway provides HTTPS termination for:

```text
roomops.local
```

The Gateway uses the `roomops-tls` Kubernetes Secret, and the HTTPRoute forwards traffic to the `roomops-api` service on port `8000`.

---

## Monitoring and Observability

RoomOps integrates Prometheus, Grafana, Loki, and Grafana Alloy.

### Prometheus

Prometheus scrapes the RoomOps `/metrics` endpoint.

Configuration includes:

- 15-second scrape interval.
- Seven-day retention.
- Persistent storage.
- Resource requests and limits.

### Grafana

Grafana provides a provisioned RoomOps dashboard.

It uses:

- Prometheus as the metrics data source.
- Loki as the log data source.
- Persistent storage.
- Kubernetes Secret-based administrator credentials.

### Loki

Loki provides centralized log storage.

The deployment uses SingleBinary mode with filesystem-backed storage and a persistent volume.

### Grafana Alloy

Grafana Alloy runs as a DaemonSet.

It:

1. Discovers Kubernetes pods.
2. Filters pod targets by node.
3. Adds namespace, pod, container, and node labels.
4. Collects container logs.
5. Pushes logs to Loki.

### Observability architecture

```mermaid
flowchart LR
    API["RoomOps API"] --> MET["/metrics"]
    MET --> PROM["Prometheus"]
    PROM --> GRAF["Grafana"]

    POD["Kubernetes Pods"] --> ALLOY["Grafana Alloy"]
    ALLOY --> LOKI["Loki"]
    LOKI --> GRAF
```

The monitoring configuration is located in:

```text
observability/
├── prometheus/
├── grafana/
├── loki/
└── alloy/
```

The current configuration is designed as a lightweight, single-replica monitoring stack rather than a highly available production observability platform.

---

## Security

Security measures implemented in RoomOps include:

### Container security

- Multi-stage Docker build.
- Non-root runtime user.
- Runtime dependency isolation.
- `.dockerignore` excludes environment files, virtual environments, tests, and evidence.
- Gunicorn instead of Flask's development server.

### Kubernetes security

- API container runs as a non-root user.
- Service account token automount is disabled for the API.
- Privilege escalation is disabled.
- Linux capabilities are dropped.
- Runtime configuration and credentials are supplied through Kubernetes Secrets.
- Resource requests and limits are configured.

### CI/CD security

- Docker Hub credentials are stored in Jenkins credentials.
- Docker authentication uses standard input for the token.
- Trivy scans container images.
- Configured HIGH and CRITICAL vulnerability findings fail the pipeline.
- Temporary CI database credentials are isolated to the test environment.

### Network exposure

- Compose host ports bind to localhost.
- Kubernetes API and database services use internal ClusterIP services.
- External application traffic is routed through the HTTPS Gateway.

---

## Testing

RoomOps uses pytest for automated testing and Ruff for static linting.

### Test coverage areas

- Health endpoint.
- Database readiness.
- Room availability.
- Reservation creation and retrieval.
- Input validation.
- Error handling.
- Prometheus metrics.
- PostgreSQL constraints.
- Concurrent reservation requests.

### Run linting

```bash
ruff check .
```

### Run the API test suite

```bash
python -m pytest -v tests/
```

### Run PostgreSQL concurrency tests

The concurrency tests require a PostgreSQL test database configured through `TEST_DATABASE_URL`.

Example:

```bash
TEST_DATABASE_URL='postgresql+psycopg://roomops:roomops@localhost:5433/roomops_test' \
python -m pytest -v -s tests/test_postgres_concurrency.py
```

The concurrency tests exercise both overlapping and non-overlapping reservation requests.

### Recorded test results

The collected evidence includes:

- Full API test suite: 24 passed.
- PostgreSQL concurrency tests: 2 passed.

See:

```text
evidence/tests/
```

---

## Backup and Recovery

Database backup and recovery are treated as operational responsibilities.

### Backup creation

The backup script is located at:

```text
scripts/backup/backup-postgres.sh
```

PostgreSQL backups use the custom archive format, which supports inspection and restoration with PostgreSQL utilities.

### Backup inspection

```bash
pg_restore --list backups/postgres/<backup-file>.dump
```

### Recovery documentation

The project includes:

- `docs/backup-and-recovery.md`
- `docs/rollback-and-recovery.md`

The documentation covers:

- PostgreSQL backup creation and validation.
- Restoration into a separate database.
- Application Helm rollback.
- Observability release rollback.
- ArgoCD Gateway configuration recovery.
- Application and database recovery checks.
- Post-recovery validation.

### Restore verification

A restore exercise was performed against a separate database named:

```text
roomops_restore_test
```

The restored database was verified to contain:

- 5 rooms.
- 3 reservations.

The production database was not modified during this restore exercise.

### Rollback considerations

Application rollback and database rollback are separate operations.

A Helm rollback does not automatically reverse database migrations or restore previous database contents.

The rollback runbook documents the recovery procedures and explicitly identifies procedures that have not yet been tested.

---

## Repository Structure

```text
roomops/
├── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── config.py
│   ├── errors.py
│   ├── extensions.py
│   └── metrics.py
│
├── argocd/
│   └── roomops-gateway.yaml
│
├── backups/
│   └── postgres/
│
├── database/
│   └── migrations/
│
├── docs/
│   ├── backup-and-recovery.md
│   └── rollback-and-recovery.md
│
├── evidence/
│   ├── ci/
│   ├── deployment/
│   ├── gitops/
│   ├── kubernetes/
│   ├── observability/
│   ├── recovery/
│   └── tests/
│
├── helm/
│   └── roomops/
│
├── k8s/
│   └── gateway/
│
├── migrations/
│   └── versions/
│
├── observability/
│   ├── alloy/
│   ├── grafana/
│   ├── loki/
│   └── prometheus/
│
├── scripts/
│   ├── backup/
│   └── seed.py
│
├── tests/
│
├── Dockerfile
├── compose.yaml
├── Jenkinsfile
├── gunicorn.conf.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
└── run.py
```

---

## Evidence and Documentation

Implementation and operational evidence is available in:

```text
evidence/
```

| Directory        | Evidence                                                        |
| ---------------- | --------------------------------------------------------------- |
| `ci/`            | Jenkins build, console output, image metadata, Trivy scan       |
| `tests/`         | API test and PostgreSQL concurrency results                     |
| `deployment/`    | Kubernetes status, HTTPS checks, application logs               |
| `gitops/`        | ArgoCD application screenshot                                   |
| `observability/` | Grafana dashboard and Loki logs                                 |
| `recovery/`      | Backup creation, restore verification, rollback procedure       |
| `kubernetes/`    | Supporting manifests, migration, database, and cluster evidence |

Additional operational documentation:

- [Backup and Recovery](docs/backup-and-recovery.md)
- [Rollback and Recovery Runbook](docs/rollback-and-recovery.md)
- [Assessment Evidence Index](evidence/README.md)

---

## Current Limitations

RoomOps is an engineering and assessment project, not a fully managed, highly available production reservation platform.

Current limitations include:

- The Kubernetes application and observability deployments use a single replica by default.
- The observability stack uses lightweight filesystem-backed Loki storage.
- ArgoCD currently manages Gateway resources rather than the application Helm release.
- Production database restoration has not been performed.
- Live Helm and ArgoCD rollback exercises remain separate from the documented procedures.
- Database migration downgrades have not been tested.
- The local Kind environment does not represent a multi-zone production Kubernetes cluster.

These limitations are documented to distinguish implemented and verified capabilities from operational procedures that still require further validation.

---

## License

See [LICENSE](LICENSE).

---

**RoomOps** — Building reliable services through automation, containerization, Kubernetes, observability, and operational discipline.
