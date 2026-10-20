# Security Policy

## Reporting a vulnerability

Do not report exploitable vulnerabilities in public issues. Until a dedicated private security
contact is configured, contact the repository owner through GitHub's private vulnerability
reporting feature (if enabled) or a private message. Include affected version/commit, impact,
reproduction steps, and any safe proof of concept. Do not include real user data or credentials.

## Supported versions

Security fixes target the latest version on the `main` branch. This is an early-stage project;
no formal service-level agreement or guaranteed response time is offered.

## Security expectations

- Never commit secrets. Values in `.env.example` are placeholders only.
- Use unique, high-entropy production secrets and restrict access to deployment credentials.
- Keep dependencies updated and review vulnerability reports before deployment.
- Enforce authenticated, owner-scoped access on every API operation.
- Use HTTPS, secure cookie/token handling, least-privilege database credentials, and production
  settings with debug disabled.
- Treat uploaded datasets and annotation payloads as untrusted input.
- Do not use real or confidential datasets in tests or public examples.
