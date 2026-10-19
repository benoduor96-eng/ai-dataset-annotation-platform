# Repository Review and RustLabs Readiness

This checklist records observable repository facts. It is not an endorsement or a guarantee of
acceptance by RustLabs; its reviewers make the final decision.

## Verified repository state

- Repository: `benoduor96-eng/ai-dataset-annotation-platform`
- Default branch: `main`
- Repository is public and is not marked as a fork (checked 2026-10-20).
- The `main` branch had 32 commits at the time of the check.
- The latest inspected GitHub Actions run completed successfully for backend, frontend, and Java
  jobs: https://github.com/benoduor96-eng/ai-dataset-annotation-platform/actions/runs/39340956135
- CI success proves only that the configured checks passed; it does not prove production readiness,
  security certification, or a specific qualifying source-line count.

## Requirements still requiring evidence or owner action

- **Qualifying original source lines:** Run `python scripts/count_source_lines.py` from a clone.
  Inspect its exclusions and compare with RustLabs' current counting rules. The repository's
  current codebase is small and is not yet verified to meet a 30,000-line minimum. Do not pad
  the repository with boilerplate, generated code, copied code, or empty commits.
- **Ownership and provenance:** The owner must confirm that each submitted source file is their
  own work or is reused under compatible terms, and retain supporting commit history.
- **AI assistance disclosure:** Disclose AI-assisted changes accurately wherever the submission
  requests it. AI assistance must not be represented as unaided human work.
- **License/permission:** No root `LICENSE` file was present at the time of review. The owner must
  choose the intended licensing terms after checking RustLabs' submission terms and any existing
  third-party licenses. Do not add an open-source license without the owner's informed choice.
- **Dependency and security review:** Current CI runs tests and builds but does not yet enforce a
  full dependency vulnerability audit, secret scan, or production deployment security review.
- **Production readiness:** Validate deployment settings, auth/tenant boundaries, backup/restore,
  observability, rate limits, and end-to-end workflows before calling this production-ready.

## Before submitting

1. Clone the repository and run the source inventory utility.
2. Review the actual counted files and remove any generated or third-party material from the
   submission if the rules exclude it.
3. Verify the repository has sufficient original, meaningful source code and a genuine history.
4. Decide and accurately state ownership, licensing, and AI-assistance disclosures.
5. Run all CI jobs and review test results, not just the green status icon.
6. Read RustLabs' current submission terms and confirm all form answers are accurate.
