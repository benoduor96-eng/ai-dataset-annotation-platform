# Testing strategy and release gates

The platform combines Django/DRF, PostgreSQL, a Java ingestion service, and a React
workspace. A change should be verified at the narrowest useful layer and then through
the full CI workflow.

## Test layers

### Python validation and service tests

Cover malformed payloads, empty values, duplicate labels, import limits, duplicate
external identifiers, and the no-partial-write guarantee for rejected imports.
Service tests should verify both the result and the database state after failure.

### API authorization and workflow tests

For each writable endpoint, test unauthenticated access, an authorized owner, and a
different user. Verify that client-supplied identity or status fields cannot bypass
server-side ownership or state-transition checks. Test valid and invalid transitions,
including submission without annotations and repeat review attempts.

### Database-backed tests

Run model and API tests against PostgreSQL in CI to catch differences that an in-memory
or SQLite-only test may miss. Migrations should apply from an empty database, and
`makemigrations --check --dry-run` should report no uncommitted model changes.

### Java service tests

Test request validation, service behavior, and expected HTTP responses. Include
invalid input and boundary cases rather than testing only the application context.

### Frontend checks

The production build must succeed. Where interaction tests are added, cover sign-in
failure, expired sessions, empty project lists, API failures, and sign-out behavior.
Do not consider a successful build a substitute for behavioral tests.

## Change-specific test checklist

- [ ] New validation has valid, invalid, and boundary examples.
- [ ] New state changes cover allowed and rejected transitions.
- [ ] New endpoints cover authentication and ownership.
- [ ] Database changes include migrations and a clean-database check.
- [ ] UI changes cover loading, empty, success, and failure states.
- [ ] Public response changes update the API contract and frontend caller.
- [ ] No credentials, private data, or real annotation payloads are committed.

## Release gates

A pull request is ready to merge only when the applicable CI jobs pass, migrations
are consistent, the diff is reviewed for authorization and privacy regressions, and
documentation describes the behavior that is actually implemented. A red or skipped
job must be investigated rather than described as a pass.

This document is a test plan. Checklist items are not evidence that a test exists;
report implemented coverage from the test files and CI results.
