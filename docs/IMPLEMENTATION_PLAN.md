# Implementation Plan

## Delivery expectation
A 3–4 week timeline is a planning target, not a guarantee. The actual schedule depends on experience, scope, integration issues, and testing. Prioritize a reliable MVP over adding speculative features.

## Phase 0 — Confirm scope and repository
Tasks:
- Review all docs and resolve open decisions.
- Create repository and `.gitignore`.
- Create frontend/backend skeleton and environment configuration.
- Add health endpoint and frontend shell.
Exit checks:
- App starts locally.
- `.env` and secrets are ignored.
- README setup instructions are accurate.

## Phase 1 — Database and authentication
Tasks:
- Configure PostgreSQL and SQLAlchemy.
- Add Alembic migrations for users, trials, participants, audit events.
- Implement password hashing, login, token/session handling, current-user endpoint.
- Enforce per-user trial authorization.
- Add auth and authorization tests.
Exit checks:
- Unauthenticated calls are rejected.
- User A cannot access User B's trials.
- Passwords are never stored or logged in plaintext.

## Phase 2 — Trial management
Tasks:
- Create/list/get trials.
- Build trial overview and create-trial UI.
- Add audit events for trial creation.
Exit checks:
- Form validation and API validation work.
- Trial ownership is enforced.
- Tests cover duplicate trial code and invalid dates.

## Phase 3 — CSV preview and import
Tasks:
- Implement file size/row limits and CSV parser.
- Validate headers, statuses, dates, integers, duplicate participant codes.
- Build preview/error table and explicit import confirmation.
- Import in transaction and record audit metadata.
Exit checks:
- Invalid structural CSV is rejected clearly.
- Invalid rows are not silently imported.
- Duplicate IDs are handled according to the approved policy.
- Oversized/malformed files fail safely.

## Phase 4 — Metrics and charts
Tasks:
- Implement a single metrics service.
- Add metric endpoint with definitions and data-quality flags.
- Build KPI cards, status chart, and optional trend chart.
Exit checks:
- Counts and rates match independently calculated test fixtures.
- Zero-participant and inconsistent-data cases are handled.
- Dashboard and PDF will use the same service.

## Phase 5 — Gemini AI insights
Tasks:
- Configure official Google Gen AI SDK via environment.
- Add an AI service abstraction, timeouts, bounded prompts, and error handling.
- Send only aggregate metrics; avoid participant rows and identifiers.
- Show AI-generated label and human-review disclaimer.
- Add mocked provider tests and a small optional integration test.
Exit checks:
- Dashboard works without an API key.
- Provider failures do not break metrics.
- AI does not claim unsupported follow-up needs or projected dates.
- Audit event is created without secrets or raw data.

## Phase 6 — PDF reports and audit log
Tasks:
- Generate PDF from server-computed metrics.
- Include definitions, timestamps, trial metadata, caveats, and optional AI narrative.
- Build permitted audit log view.
Exit checks:
- PDF totals match metrics endpoint.
- Export action is audited.
- Audit view enforces access rules.

## Phase 7 — Hardening and deployment
Tasks:
- Add Dockerfiles and Docker Compose.
- Add health checks, environment validation, CORS restrictions, logging.
- Run backend/frontend tests, lint/type checks, dependency checks.
- Document deployment to a selected provider only after one is approved.
Exit checks:
- Fresh setup works from README.
- No secrets in repository.
- All required acceptance criteria have test evidence.
- Limitations and remaining risks are documented.

## Suggested week allocation
- Week 1: Phase 0–2
- Week 2: Phase 3–4
- Week 3: Phase 5–6
- Week 4: Phase 7, bug fixing, demo preparation
This is an estimate; reduce scope rather than skip security or validation.

## Change control
Any major stack change, public deployment, real-data use, clinical decision-support feature, or destructive data operation requires user approval.
