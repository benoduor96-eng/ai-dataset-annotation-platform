# AI Dataset Annotation Platform

A full-stack platform for dataset projects, annotation schemas, task assignment,
human labeling, quality review, workflow metrics and JSON export.

## Architecture

- Django + Django REST Framework provide the authenticated API and workflow services.
- PostgreSQL stores projects, datasets, tasks, annotations and review decisions.
- Redis/Celery are configured as the execution layer for future asynchronous jobs; background
  import and AI task execution are not yet implemented end to end.
- Java 21 + Spring Boot provides a separate ingestion-service scaffold.
- React + Vite provides the annotation workspace.
- Docker Compose provides a local multi-service environment.

## Implemented capabilities

- JWT sign-in for the React workspace and API clients.
- Project ownership scoping and validation of cross-project relationships.
- Dataset and schema management with input validation.
- Task claim, submit and review transitions enforced in transactional services.
- Annotation confidence validation and duplicate-label detection.
- Bounded bulk task import with validation before writes.
- Project workflow metrics and JSON annotation export.
- Exact-match inter-annotator agreement metrics for tasks labeled by distinct annotators.
- Schema-aware quality checks for classification, named entities, bounding boxes and segmentation polygons.
- Per-annotation quality issue codes and project-task quality summaries, without mutating annotations.
- Structured project audit trail for task claim/submission/review, annotation create/update, bulk imports, and version creation.
- Immutable dataset snapshots containing schema/task/annotation state, deterministic SHA-256 content hashes, sequential version numbers, and owner-scoped history.
- Owner-scoped, read-only audit-event API with event-type and object filters; event payloads avoid copying annotation content.
- CI checks for Python compilation, Django configuration and migrations, backend tests,
  Java tests, frontend production build, and source-file inventory reporting.

## Quick start

1. Copy the sample environment file and replace the development secret with a unique
   random value: `cp .env.example .env`.
2. Start the services: `docker compose up --build`.
3. Open the frontend at http://localhost:5173 and the Django API at http://localhost:8000/api/.

Create a Django user before signing in to the frontend:

    docker compose exec backend python manage.py createsuperuser

The API token endpoint is `/api/auth/token/`. Supply the username and password to
receive a JWT access token. The frontend stores the access token in browser local
storage for this development build; production should assess an HttpOnly cookie
session or another hardened token-storage strategy.

## API highlights

- POST `/api/auth/token/` — obtain JWT tokens.
- POST `/api/auth/token/refresh/` — refresh an access token.
- GET/POST `/api/projects/` — list or create projects.
- GET `/api/projects/{id}/metrics/` — project task, review, confidence, and agreement metrics.
- GET/POST `/api/datasets/` — list or create datasets.
- POST `/api/datasets/{id}/import/` — import up to 500 task rows.
- GET/POST `/api/datasets/{id}/versions/` — list snapshots or create an immutable snapshot of the current dataset state.
- GET/POST `/api/schemas/` — manage annotation schemas.
- GET/POST `/api/tasks/` — list or create annotation tasks.
- POST `/api/tasks/{id}/claim/` — claim a task.
- POST `/api/tasks/{id}/submit/` — submit a task with at least one annotation.
- POST `/api/tasks/{id}/review/` — approve or reject a submitted task.
- POST `/api/tasks/{id}/quality-check/` — validate saved annotations against a schema.
- GET/POST `/api/annotations/` — manage annotation data.
- GET `/api/projects/{id}/export/` — export a project as JSON.
- GET `/api/audit-events/` — list audit events for owned projects; supports `event_type`, `object_type`, and `object_id` query filters.
- GET `/api/health/` — health endpoint.

### Annotation quality checks

Send an optional `schema_id` in the JSON request body to choose a schema attached to
the task's dataset. If omitted, the first schema by ID is used. The endpoint reports
whether each annotation passes, issue codes and paths, counts of valid/invalid
annotations, and the overall validity rate. It supports these canonical data shapes:

- Classification: `{"label": "cat"}`
- Named entities: `{"entities": [{"start": 0, "end": 3, "label": "PERSON"}]}`
- Bounding boxes: `{"boxes": [{"x_min": 1, "y_min": 2, "x_max": 10, "y_max": 12, "label": "car"}]}`
- Segmentation: `{"segments": [{"label": "road", "points": [[0, 0], [1, 0], [1, 1]]}]}`

Coordinates may be pixels or normalized values; the validator checks structure and
ordering without assuming image dimensions. These checks are a configurable quality
signal, not a substitute for task-specific policy or human review.

### Audit trail

The audit trail stores structured events alongside workflow transactions, so a rolled-back
task change does not leave a success event. Events include the project, actor where available,
event type, object type/ID, timestamp, and minimal metadata. The API is read-only and limits
results to projects owned by the authenticated user. Example filters include
`/api/audit-events/?event_type=task.reviewed` and
`/api/audit-events/?object_type=task&object_id=12`. Audit metadata should not contain
credentials, raw dataset content, or full annotation payloads. The table is append-only through
the application API, but database administrators can still alter database records; production
deployments needing tamper evidence should export events to separately controlled storage.

### Dataset versioning

Create a snapshot with `POST /api/datasets/{id}/versions/` and an optional
`{"change_note": "reviewed labels for release candidate"}` body. Each snapshot contains
the dataset's schemas, tasks, task payloads, current workflow states, and annotations.
A canonical JSON representation is hashed with SHA-256; unchanged content has the same
hash even when another numbered snapshot is created. The monotonically increasing version
number identifies the snapshot sequence, while the hash identifies its content. Snapshots
are read-only through this API and can be listed with `GET /api/datasets/{id}/versions/`.
This initial version records snapshots but does not implement restoration or storage
deduplication. Because manifests may contain dataset content, restrict access and follow
the project's data-retention policy.

### Inter-annotator agreement

The project metrics endpoint reports `annotation_agreement` with the number of tasks
annotated by multiple distinct annotators, pairwise comparisons, and the fraction of
annotation pairs whose normalized JSON data matches exactly. The score is `null` when
there are no eligible comparisons. This is a basic quality signal, not Cohen's kappa,
and it does not account for label-specific severity or chance agreement.

See `docs/ARCHITECTURE.md` for service boundaries, endpoint behavior, security notes
and known limitations. See `docs/DEVELOPMENT_PLAN.md` for the staged implementation
roadmap.

## Backend development

    cd backend
    python -m venv .venv
    # Windows: .venv\Scripts\activate
    # Linux/macOS: source .venv/bin/activate
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py runserver

Set `DJANGO_SECRET_KEY`, database connection variables, and `DJANGO_DEBUG=true` for
local development. Production deployments must set `DJANGO_DEBUG=false`, a unique
secret and explicit `DJANGO_ALLOWED_HOSTS`.

## Frontend development

    cd frontend
    npm install
    npm run dev

## Tests and source inventory

From the repository root, run:

    python scripts/count_source_lines.py

The inventory excludes migrations, common build/dependency folders and files marked generated.
It is an estimate for review, not an official RustLabs count. CI runs Django's test discovery
to include both `tests.py` and `test_*.py` files.

To run the backend suite locally:

    cd backend
    python manage.py test apps.api

## Security and ownership

Never commit `.env`, production credentials, access tokens, private dataset contents
or client data. Review third-party licenses and preserve provenance for imported code.
AI assistance was used while developing this repository; maintain an accurate account
of AI-assisted changes and verify that all code is permitted for your intended use.
This project is in active development and does not claim production readiness or guarantee
acceptance by any external codebase review program.


## Team workflows and configurable quality rules

Project owners can manage workspace membership with `GET/POST /api/projects/{id}/members/` and remove a member with `DELETE /api/projects/{id}/members/{user_id}/`. Roles are `admin`, `annotator`, and `reviewer`. Membership metadata is available now; other data endpoints remain owner-scoped until role-aware authorization is applied consistently.

Dataset owners can create/list rules at `GET/POST /api/datasets/{id}/quality-rules/`. Supported rule types are `min_confidence` (`parameters.minimum`, 0–1), `require_non_empty`, `allowed_labels` (`parameters.labels`), and `max_annotations` (`parameters.maximum`). Enabled rules are applied during `POST /api/tasks/{id}/quality-check/`. `GET /api/tasks/review-queue/` lists submitted tasks awaiting review and accepts an optional `dataset_id` filter.


## Dataset restoration

Dataset owners can restore a saved snapshot with `POST /api/datasets/{dataset_id}/versions/{version_number}/restore/` and JSON body `{"confirm": true}`. This operation replaces the dataset's schemas, task set, and annotations with the snapshot state in one database transaction and writes a `dataset.version_restored` audit event. The explicit confirmation is required because tasks created after the snapshot can be deleted. If an annotator or assignee account has been deleted, its historical assignment is skipped during restoration.


## Project reporting and signed integrations

`GET /api/projects/{id}/report/` returns the project metrics plus dataset-level workflow counts, enabled quality-rule counts, and saved-version counts.

Trusted external systems can submit task batches to `POST /api/integrations/webhooks/tasks/`. Set `INTEGRATION_WEBHOOK_SECRET` in the backend environment and send `X-Platform-Signature: sha256=<hex>`, where the hex value is the HMAC-SHA256 of the exact raw JSON request body. The body shape is `{"dataset_id": 123, "tasks": [{"external_id": "source-1", "payload": {"text": "example"}}]}`. Requests fail closed when the secret is unset or the signature is invalid. Treat the shared secret as a production credential and rotate it if exposed.
