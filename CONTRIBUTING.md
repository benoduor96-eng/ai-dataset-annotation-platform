# Contributing

Thank you for considering a contribution to the AI Dataset Annotation Platform.

## Before opening a change

1. Open or identify an issue describing the problem or feature.
2. Keep pull requests focused and explain the user-visible behavior.
3. Add or update tests for behavior changes and bug fixes.
4. Update documentation and API contracts when interfaces change.
5. Never commit secrets, real annotation data, customer data, or private credentials.

## Local validation

Backend:

```bash
cd backend
python -m pip install -r requirements.txt
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest apps/api
```

Frontend:

```bash
cd frontend
npm install
npm run build
```

Java ingestion service:

```bash
cd java-service
mvn test
```

From the repository root, run `python scripts/count_source_lines.py` to generate a transparent
source-file inventory. This inventory is an estimate, not a certification of any third party's
line-count rules.

## Pull request checklist

- [ ] Tests cover the behavior changed.
- [ ] No generated, vendored, or unrelated files were added to inflate metrics.
- [ ] Documentation and configuration are updated.
- [ ] Security and tenant-boundary implications were considered.
- [ ] Any AI-assisted contribution is disclosed accurately where requested.
