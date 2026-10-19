# Architecture and service boundaries

## Overview

Django REST Framework owns project, dataset, task, annotation and review workflows.
PostgreSQL is the system of record. Redis/Celery is reserved for asynchronous work.
The Java Spring Boot service is an ingestion boundary, and React/Vite is the operator
workspace.

## Domain model

- Project belongs to one owner and is the tenant boundary in this version.
- Dataset belongs to a project and tracks imported task count.
- AnnotationSchema defines label types and a versioned set of labels.
- AnnotationTask stores an external identifier, payload, assignee, AI suggestions
  and workflow status.
- Annotation stores structured output and optional confidence.
- Review records a reviewer decision for one annotation.

Project ownership is enforced in queryset filtering and serializer validation.
Never accept owner, annotator, reviewer, assignee or workflow status from a client
as authoritative identity or workflow state.

## Task lifecycle

pending -> in_progress -> submitted -> approved or rejected

The service layer performs transitions inside database transactions. A task cannot
be submitted until at least one annotation exists. A review is only accepted for a
submitted task and records the decision against each annotation.

## API endpoints

All endpoints except health and token acquisition require a valid JWT.

| Endpoint | Purpose |
|---|---|
| POST /api/auth/token/ | Obtain access and refresh tokens |
| GET/POST /api/projects/ | List or create owned projects |
| GET /api/projects/{id}/metrics/ | Owned-project workflow summary |
| GET/POST /api/datasets/ | List or create datasets within owned projects |
| POST /api/datasets/{id}/import/ | Atomically import up to 500 tasks |
| GET/POST /api/schemas/ | Manage annotation schemas |
| GET/POST /api/tasks/ | List or create tasks in owned datasets |
| POST /api/tasks/{id}/claim/ | Claim a pending task |
| POST /api/tasks/{id}/submit/ | Submit a task with annotations |
| POST /api/tasks/{id}/review/ | Approve or reject a submitted task |
| GET/POST /api/annotations/ | Create and inspect annotation data |
| GET/POST /api/reviews/ | Inspect or create review records |
| GET /api/projects/{id}/export/ | Export annotation rows as JSON |

## Bulk import contract

POST /api/datasets/12/import/ accepts a body with a tasks list. Each row contains
external_id and payload, for example:

    {"tasks":[{"external_id":"image-001","payload":{"image_url":"https://example.test/1.jpg"}}]}

The operation validates the full batch before writing. IDs must be non-empty,
at most 160 characters, unique in the request and unused in the platform. Payloads
must be non-empty JSON objects. The per-request limit is 500 rows to bound memory
and transaction duration.

## Security and privacy

- Keep DJANGO_SECRET_KEY, database credentials and provider keys in environment
  variables or a secret manager; never commit production values.
- Set DJANGO_DEBUG=false and explicitly configure DJANGO_ALLOWED_HOSTS in deployment.
- Use HTTPS in production and restrict CORS to the deployed frontend origin.
- Treat uploaded text, images, model suggestions and annotations as potentially
  sensitive dataset content. Apply retention and access policies before production use.
- Exports include annotation content and annotator identifiers; only project owners
  can export their own project. Add de-identification before external sharing.
- Use least-privilege service credentials and rotate compromised secrets immediately.

## Current limitations and next milestones

This branch is an incremental foundation, not a claim of production readiness.
Organization/team membership, object-storage upload handling, typed schema validation,
durable Celery jobs, rate limiting, audit-event retention, Java integration tests,
and deployment observability remain follow-up work. Add them as tested capabilities
rather than documentation-only claims.
