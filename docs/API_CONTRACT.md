# API contract

This document records the currently exposed API surface. Treat it as a contract for
frontend and integration work; update it when serializers, routes, or response shapes
change. The API is served under `/api/` by Django REST Framework.

## Authentication

- `POST /api/auth/token/`: exchange username and password for JWT tokens.
- `POST /api/auth/token/refresh/`: exchange a refresh token for a new access token.
- Send authenticated requests with `Authorization: Bearer <access-token>`.
- Never put credentials or live tokens in logs, fixtures, screenshots, or issue reports.

## Resource endpoints

| Resource | Methods / action | Purpose |
| --- | --- | --- |
| Projects | `GET, POST /api/projects/` | List owned projects or create a project |
| Project metrics | `GET /api/projects/{id}/metrics/` | Read task/review workflow metrics |
| Datasets | `GET, POST /api/datasets/` | List accessible datasets or create a dataset |
| Dataset import | `POST /api/datasets/{id}/import/` | Validate and import a bounded batch of task rows |
| Schemas | `GET, POST /api/schemas/` | List or define annotation schemas |
| Tasks | `GET, POST /api/tasks/` | List accessible tasks or create a task |
| Claim task | `POST /api/tasks/{id}/claim/` | Claim a pending task |
| Submit task | `POST /api/tasks/{id}/submit/` | Submit a task with annotation data |
| Reviews | Read-only review endpoint | Read review records; decisions use workflow actions |

The exact writable fields are defined by serializers and service functions. Client
payloads must not be treated as authoritative for owner, annotator, reviewer, assignee,
or workflow status. Server-side ownership and transition checks are mandatory even
when the UI hides an action.

## Import payload

A dataset import accepts a non-empty list of rows. Each row contains an
`external_id` and a JSON-object `payload`, for example:

```json
[
  {
    "external_id": "sample-0001",
    "payload": {"text": "A sample sentence"}
  }
]
```

The current import service limits a request to 500 rows, validates the batch before
writing, and rejects duplicate external identifiers within a batch. Callers should
surface validation errors to users and must not assume partial success.

## Workflow semantics

The expected task lifecycle is:

`pending -> in_progress -> submitted -> approved | rejected`

Use the claim, submit, and review service actions rather than directly editing status
fields. A task submission requires annotation data. Review decisions are restricted to
the supported decision values and should be attributable to the authenticated reviewer.

## Error handling and compatibility

- Treat 2xx responses as success and parse the response body according to the endpoint.
- Treat 400 responses as user-correctable validation errors.
- Treat 401 responses as missing or expired authentication; refresh or sign in again.
- Treat 403 responses as authorization failures; do not retry with altered ownership data.
- Treat 404 responses as a missing or inaccessible resource.
- Treat 5xx responses as service failures; show a safe message and retain user work locally.
- Clients should not depend on undocumented database fields or internal service exceptions.

Before changing a response shape, update this document, serializers/tests, and the
frontend caller in the same pull request.
