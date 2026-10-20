# Repository Review and RustLabs Readiness

This checklist records observable repository facts. It is not an endorsement or a guarantee of
acceptance by RustLabs; its reviewers make the final decision.

## Verified repository state

- Repository: `benoduor96-eng/ai-dataset-annotation-platform`
- Default branch: `main`
- Repository is public and is not marked as a fork (checked 2026-10-20).
- The `main` branch had 32 commits at the time of the initial check.
- CI passed all four jobs (backend, frontend, Java, and source inventory) on the readiness branch
  at commit `37797b8519e8e7a311f09f986aa4d22535bd0099`.
- The earlier baseline inventory reported 1,244 physical source lines and 1,074 nonblank lines
  across 40 files. After the quality-control, audit-trail, and dataset-versioning expansions, the
  inventory at commit `3cba8f5efeda365848f2bcf87e0c9f3f36c12665` reported **2,191 physical source
  lines and 1,907 nonblank source lines across 47 files** under the script's rules. This is still
  an estimate, not an official RustLabs count, and the estimator may not include every suffix
  RustLabs counts. The 30,000-line target remains unmet.
- The readiness branch also adds schema-aware quality checks for classification, named entities,
  bounding boxes and segmentation, plus a task-level quality-check endpoint and tests.
- A further feature adds project audit events for task claim/submission/review, annotation
  create/update, bulk imports, and dataset version creation; an owner-scoped read-only endpoint;
  and regression tests for tenant isolation, filtering, and read-only behavior.
- Dataset versioning now creates immutable JSON snapshots with canonical SHA-256 hashes, ordered
  version numbers, annotation counts, change notes, and owner-scoped history. Regression tests
  cover hash stability, changed content, access control, and event creation. The source inventory
  and test status must be read from the latest successful CI run.
- CI success proves only that configured checks passed; it does not prove production readiness,
  security certification, or acceptance by RustLabs.

## Requirements still requiring evidence or owner action

- **Qualifying original source lines:** The observed 1,244 physical lines are far below a 30,000-line
  target. Under this estimate, the gap is approximately 28,756 lines, before accounting for any
  differences in RustLabs' inclusion rules. The platform needs substantial real features, tests,
  and maintainable implementation—not boilerplate, generated code, copied code, or empty commits.
- **Ownership and provenance:** The owner must confirm that each submitted source file is their
  own work or is reused under compatible terms, and retain supporting commit history.
- **AI assistance disclosure:** Disclose AI-assisted changes accurately wherever the submission
  requests it. AI assistance must not be represented as unaided human work.
- **License/permission:** No root `LICENSE` file was present at the time of review. The owner must
  choose the intended licensing terms after checking RustLabs' current submission terms and any
  third-party licenses. No license is added automatically because the choice affects rights.
- **Dependency and security review:** Dependabot proposes dependency updates, but this is not a
  complete vulnerability audit or secret scan. Review update PRs and run a dedicated security
  review before submission.
- **Production readiness:** Validate deployment settings, auth/tenant boundaries, backup/restore,
  observability, rate limits, and end-to-end workflows before calling this production-ready.

## Before submitting

1. Clone the repository and run `python scripts/count_source_lines.py`.
2. Review the actual counted files and compare the estimator with RustLabs' current counting rules.
3. Build enough original, meaningful functionality to satisfy the qualifying source threshold.
4. Verify ownership, third-party license compatibility, and AI-assistance disclosures.
5. Run all CI jobs and review their test results, not just the green status icon.
6. Choose a license only after deciding what rights you intend to grant and checking submission terms.
7. Read RustLabs' current submission terms and confirm all form answers are accurate.
