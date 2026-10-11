# Antigravity Agent Instructions

## Project mission
Build a maintainable portfolio MVP for a clinical-trial operational dashboard using React + TypeScript, FastAPI, PostgreSQL, SQLAlchemy, Google Gemini, CSV processing, and PDF export.

## Before changing code
1. Read `README.md` and the relevant documents in `docs/`.
2. Inspect the current repository, dependency manifests, tests, and existing conventions before editing.
3. Confirm the current phase in `docs/IMPLEMENTATION_PLAN.md`.
4. If a critical requirement conflicts across files, stop and explain the conflict rather than silently choosing.
5. Do not replace working architecture or add major dependencies without explaining why and requesting approval.

## Implementation rules
- Implement incrementally, one phase or vertical slice at a time.
- Use TypeScript for React components and strict typing where practical.
- Keep UI, API client, domain types, and reusable components separated.
- Use FastAPI routers, Pydantic request/response schemas, service functions, and SQLAlchemy models with clear responsibilities.
- Use Alembic for database migrations. Do not rely on manual schema changes in production.
- Keep secrets in environment variables. `.env` must be git-ignored; `.env.example` contains placeholders only.
- Never hardcode API keys, passwords, JWT secrets, or production URLs.
- Validate and constrain all uploaded files: extension/content, size, required columns, data types, allowed statuses, duplicates, and row-level errors.
- Do not trust frontend validation alone.
- Use parameterized ORM queries; avoid unsafe SQL construction.
- Hash passwords with a modern password-hashing library. Never store or log plaintext passwords.
- Enforce authorization on every protected endpoint; hiding UI controls is not authorization.
- Add audit events for login outcomes and relevant data-changing/export/AI actions without recording secrets or unnecessary participant-level details.
- Send only aggregated, minimized metrics to Gemini. Never send raw CSV rows or participant identifiers.
- Treat AI responses as untrusted content: validate output structure, handle provider failures/timeouts, and render as text rather than executable HTML.
- Do not claim an AI-generated finding is clinically validated. Include caveats and human-review messaging.
- Do not invent follow-up needs, dropout explanations, completion dates, or risk scores when the underlying data does not support them.
- Generate PDF reports from validated metrics and clearly label AI-generated content and generation time.
- Provide useful error messages without leaking stack traces, secrets, or internal configuration.

## Quality gates
- Add tests for each feature and bug fix.
- Run formatter/linter/type checks and relevant tests before declaring completion.
- Report commands run, results, failures, and known limitations honestly.
- Do not claim tests passed if they were not executed.
- Keep `README.md`, API docs, and other specifications in sync with actual behavior.
- Do not delete tests, data, migrations, or user work merely to make checks pass.
- Avoid unrelated refactors and generated files that are not needed.

## Definition of done for each phase
- Acceptance criteria for that phase are met.
- Tests cover normal cases, invalid input, permissions, and failure paths as applicable.
- No secrets are committed.
- User-visible behavior and configuration are documented.
- Any remaining limitations are listed clearly.

## Approval required
Ask before adding paid services, deploying publicly, changing the approved stack, introducing real clinical/patient data, performing destructive operations, or implementing features that imply clinical decision support or regulatory validation.
