# AI Dataset Annotation Platform

A full-stack platform for creating datasets, defining annotation schemas, assigning annotation tasks, reviewing labels, exporting datasets, and integrating AI-assisted pre-annotation.

## Architecture

- **Django + Django REST Framework** — core platform, auth, projects, datasets, annotation workflow and exports.
- **PostgreSQL** — primary database.
- **Redis/Celery** — asynchronous AI/export jobs.
- **Java 21 + Spring Boot** — ingestion/processing service for high-throughput dataset imports and future model-serving integrations.
- **React + Vite** — annotation workspace and dashboard.
- **Docker Compose** — local development stack.

## Core features

- JWT authentication
- Organizations and projects
- Dataset/file management
- Configurable annotation schemas
- Task assignment and status tracking
- Text classification, entity and bounding-box-ready schema model
- Human annotation + reviewer workflow
- AI suggestion storage with confidence scores
- Dataset export endpoint
- Java ingestion API
- Health checks and CI

## Quick start

```bash
git clone <your-repository-url>
cd ai-dataset-annotation-platform
cp .env.example .env
docker compose up --build
```

Frontend: http://localhost:5173
Django API: http://localhost:8000/api/
Django admin: http://localhost:8000/admin/
Java ingestion service: http://localhost:8080/

## API highlights

- `POST /api/auth/register/`
- `POST /api/auth/token/`
- `GET /api/projects/`
- `POST /api/projects/`
- `GET /api/datasets/`
- `POST /api/datasets/`
- `GET /api/tasks/`
- `POST /api/annotations/`
- `POST /api/tasks/{id}/submit/`
- `POST /api/tasks/{id}/review/`
- `GET /api/projects/{id}/export/`
- `GET /api/health/`

## Development

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Java service:

```bash
cd java-service
./mvnw spring-boot:run
```

Frontend:

```bash
npm install
npm run dev
```

## Security

Secrets are loaded from environment variables. Do not commit `.env`, credentials, API keys, model keys, or production secrets.
