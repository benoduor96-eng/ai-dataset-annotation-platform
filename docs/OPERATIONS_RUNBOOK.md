# Operations runbook

## Local startup

1. Install Docker Desktop / Docker Engine with the Compose plugin.
2. Copy `.env.example` to `.env` and replace development-only secrets.
3. Start the stack with `docker compose up --build`.
4. Wait for PostgreSQL and application services to become healthy.
5. Create a Django administrator with
   `docker compose exec backend python manage.py createsuperuser`.
6. Open the Vite workspace at `http://localhost:5173` and the API at
   `http://localhost:8000/api/`.

Use the commands in the README as the source of truth if service names change.

## Routine verification

From the repository root:

- Run `docker compose ps` to inspect container state.
- Run `docker compose logs --tail=200 backend` to inspect recent backend output.
- Run `docker compose exec backend python manage.py check` for Django configuration.
- Run `docker compose exec backend python manage.py migrate --check` to detect
  unapplied migrations where supported by the installed Django version.
- Run the repository CI workflow before merging changes.

Do not publish raw logs if they contain tokens, user data, or annotation payloads.

## Common recovery paths

### API returns 401

Confirm the user exists, credentials are correct, the access token has not expired,
and the client sends the Bearer token. Do not disable authentication as a workaround.

### API returns 403 or a resource is missing

Verify the user owns the project or has the required role. Cross-tenant denial is
expected behavior and should not be "fixed" by widening querysets.

### Database migration fails

Back up persistent data before any manual intervention. Review the migration and
model diff, run the migration consistency check in CI, and reproduce the failure in a
disposable environment. Never delete a production database to make migrations pass.

### Import request is rejected

Check that the batch is non-empty, within the 500-row limit, each row has an external
identifier and a non-empty JSON-object payload, and identifiers are unique. Correct
the input and retry; the import service validates before writes.

### Service will not start

Check environment variables, database readiness, dependency installation, and the
first error in the service logs. Avoid repeatedly restarting a failing service without
capturing the underlying error.

## Security and data handling

- Use unique secrets outside development and rotate exposed credentials immediately.
- Keep database backups encrypted and limit access to authorized operators.
- Collect only data required for the annotation task and define retention before
  importing real-world personal data.
- Do not use production data in tests or public issue reports.
- Treat exported annotation files as potentially sensitive and share them only through
  approved channels.

This runbook describes local/development operations. It is not a certification that
production deployment, backup restoration, alerting, or disaster recovery has been
implemented or tested.
