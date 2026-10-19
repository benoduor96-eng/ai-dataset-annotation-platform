# Development plan

This plan describes real milestones for growing the platform without padding source
files or manufacturing history. Each milestone should be implemented, reviewed and
tested before it is considered complete.

## Milestone A — API safety and workflow invariants

- [x] Keep project queries scoped to the authenticated owner.
- [x] Validate cross-project relationships before create/update.
- [x] Make identity and workflow fields read-only in client serializers.
- [x] Centralize claim, submit and review transitions in transactional services.
- [x] Require annotations before task submission.
- [x] Add confidence and schema-label validation.
- [x] Add bulk task import with validation and bounded batch size.
- [x] Add project-level workflow metrics.
- [ ] Run database-backed tests in CI and verify a clean full-stack environment.

## Milestone B — Complete annotation experience

- [ ] Add pagination, filtering, ordering and search contracts to task endpoints.
- [ ] Add typed annotation payload validation for classification, NER, boxes and masks.
- [ ] Add task leases, assignment queues, timeout handling and reassignment history.
- [ ] Add annotation version history and optimistic concurrency checks.
- [ ] Add adjudication and reviewer conflict resolution.
- [ ] Add golden-set quality measurements and inter-annotator agreement.
- [ ] Add CSV/JSONL import and streaming export with schema validation.

## Milestone C — Data lifecycle and collaboration

- [ ] Add team membership and role-based permissions with organization-level tenancy.
- [ ] Add upload metadata, object-storage integration, checksum validation and quotas.
- [ ] Add configurable retention, deletion workflows and export de-identification.
- [ ] Add immutable audit events for security-sensitive actions.
- [ ] Add dataset snapshots, provenance and reproducible version comparisons.

## Milestone D — Reliability and operations

- [ ] Add idempotency keys to import and asynchronous jobs.
- [ ] Add retry-safe Celery tasks, dead-letter handling and job status endpoints.
- [ ] Add API throttling, structured logs, tracing and operational dashboards.
- [ ] Add service-to-service authentication and integration tests for Java ingestion.
- [ ] Add dependency, secret and container scanning in CI.
- [ ] Run database migration checks and end-to-end tests from a clean clone.

## Verification gates

A milestone is complete only when its tests pass, the docs describe actual behavior,
and its changes are reviewed. Source-line totals are measured from real application
code and tests; generated files, vendored dependencies, lockfiles and copied material
must not be counted as original implementation. Keep an accurate disclosure of any
AI-assisted development and verify licenses and ownership before external submission.
