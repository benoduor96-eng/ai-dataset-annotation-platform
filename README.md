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
- GET/POST `/api/schemas/` — manage annotation schemas.
- GET/POST `/api/tasks/` — list or create annotation tasks.
- POST `/api/tasks/{id}/claim/` — claim a task.
- POST `/api/tasks/{id}/submit/` — submit a task with at least one annotation.
- POST `/api/tasks/{id}/review/` — approve or reject a submitted task.
- GET/POST `/api/annotations/` — manage annotation data.
- GET `/api/projects/{id}/export/` — export a project as JSON.
- GET `/api/health/` — health endpoint.

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
