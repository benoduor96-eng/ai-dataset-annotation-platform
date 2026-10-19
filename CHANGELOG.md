# Changelog

Notable project changes are documented here. This changelog describes committed repository
changes; it does not imply a production deployment.

## Unreleased

- Added API contract, annotation guidelines, operations runbook, and testing strategy.
- Added Django domain-model tests and service-level tests.
- Added a reproducible source-file inventory utility for repository review.
- Added contribution, security-reporting, and project conduct guidance.
- CI currently validates Django configuration and tests, Java tests, and the frontend build.

## 0.1.0 — initial development

- Established Django REST API and PostgreSQL-backed project/dataset/task models.
- Added annotation task claim, submit, and review workflow services.
- Added JSON export and bounded bulk task import.
- Added React/Vite workspace and a Spring Boot ingestion-service scaffold.
