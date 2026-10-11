# Phase 3 Audit and Gap Report: CSV Import & Preview

## Scope reviewed

This audit was limited to Phase 3 requirements from the project docs and the current repository state. It does not modify application code or database schema.

Documents reviewed:
- [docs/IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- [docs/ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md)
- [docs/API_SPEC.md](API_SPEC.md)
- [backend/app/main.py](../backend/app/main.py)
- [backend/app/api/auth.py](../backend/app/api/auth.py)
- [backend/app/api/trials.py](../backend/app/api/trials.py)
- [backend/app/api/deps.py](../backend/app/api/deps.py)
- [backend/app/models/participant.py](../backend/app/models/participant.py)
- [backend/app/models/trial.py](../backend/app/models/trial.py)
- [backend/app/models/audit_event.py](../backend/app/models/audit_event.py)
- [backend/app/core/config.py](../backend/app/core/config.py)
- [backend/app/services/audit_service.py](../backend/app/services/audit_service.py)
- [frontend/src/App.tsx](../frontend/src/App.tsx)
- [tests/backend](../tests/backend)

## Executive summary

Phase 3 requirements are not yet implemented in the current codebase, even though the project already contains the foundational Phase 1 and 2 building blocks:
- user authentication and ownership are implemented,
- trial-create/list/get/update behavior exists,
- participant model and database schema exist,
- audit event infrastructure exists,
- but there is no CSV preview/import pipeline, no upload API endpoints, no validation logic, no preview UI, and no Phase 3 tests.

The repository is therefore in a state of partial readiness for Phase 3: the database and auth/trial architecture are in place, but the Phase 3 operational flow is still missing.

## Final implementation status (post-audit verification)

The Phase 3 CSV import and preview workflow was implemented and verified in the working codebase after the audit confirmed the gap.

Key implementation evidence:
- Backend preview and import endpoints were added in [backend/app/api/trials.py](../backend/app/api/trials.py).
- CSV validation and import logic were implemented in [backend/app/services/participant_service.py](../backend/app/services/participant_service.py).
- The participant database model already supported the required fields and uniqueness checks in [backend/app/models/participant.py](../backend/app/models/participant.py).
- Audit metadata sanitization and event recording were connected to participant import flows in [backend/app/services/audit_service.py](../backend/app/services/audit_service.py).
- The frontend upload/preview/confirm flow is implemented in [frontend/src/pages/ImportPage.tsx](../frontend/src/pages/ImportPage.tsx), with client helpers in [frontend/src/api/client.ts](../frontend/src/api/client.ts).
- Route wiring was updated in [frontend/src/App.tsx](../frontend/src/App.tsx).

Verified behavior:
- backend suite result: 44 passed in 13.39s using `.\.venv\Scripts\python -m pytest -q`
- frontend production build result: successful via `npm run build` in [frontend/package.json](../frontend/package.json)

Remaining limitation:
- No dedicated frontend automated test suite is configured in this repository. The project currently has a build-only validation path for the UI, not a Jest/Vitest test run.

## Requirement-by-requirement status

| Requirement | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Required CSV headers | Missing | [backend/app/models/participant.py](../backend/app/models/participant.py), [backend/alembic/versions/9743b997d217_create_initial_schema.py](../backend/alembic/versions/9743b997d217_create_initial_schema.py) | The schema defines participant fields, but no CSV parser or header validation exists. |
| Supported participant statuses | Partially implemented | [backend/app/models/participant.py](../backend/app/models/participant.py) | The model stores `status` as a string, but no allowlist enforcement or validator exists. |
| Date and integer validation | Missing | [backend/app/models/participant.py](../backend/app/models/participant.py) | Date and integer columns exist, but no validation/normalization layer exists. |
| Negative visit counts | Missing | [backend/app/models/participant.py](../backend/app/models/participant.py) | There is no validation logic for `visits_completed` / `visits_planned` bounds. |
| Duplicate participant codes | Partially implemented | [backend/app/models/participant.py](../backend/app/models/participant.py) and migration file | Unique constraint exists at the database level (`trial_id` + `participant_id`), but no upload-time duplicate detection or user-facing error handling is implemented. |
| File-size and row-count limits | Partially implemented | [backend/app/core/config.py](../backend/app/core/config.py) | `MAX_UPLOAD_MB` and `MAX_CSV_ROWS` are configured, but no route or upload validation uses them. |
| Preview without database writes | Missing | [backend/app/api](../backend/app/api), [backend/app/main.py](../backend/app/main.py), [frontend/src/App.tsx](../frontend/src/App.tsx) | No preview endpoint or preview UI exists. |
| Explicit import confirmation | Missing | [backend/app/api](../backend/app/api), [frontend/src](../frontend/src) | No import confirmation workflow exists. |
| Atomic database transaction | Missing | [backend/app/api](../backend/app/api), [backend/app/services](../backend/app/services) | There is no import service or transaction wrapper for participant insertion. |
| Trial ownership and auth on CSV endpoints | Implemented foundation only | [backend/app/api/deps.py](../backend/app/api/deps.py), [backend/app/api/trials.py](../backend/app/api/trials.py) | Authorization framework exists, but no CSV endpoints use it. |
| Audit metadata without raw CSV data | Partially implemented | [backend/app/services/audit_service.py](../backend/app/services/audit_service.py) | Sanitization rules exist, but no CSV import audit events are emitted. |
| Frontend import page and preview UI | Missing | [frontend/src/App.tsx](../frontend/src/App.tsx), [frontend/src/pages](../frontend/src/pages) | The `/import` route still renders a placeholder. |
| Backend CSV import API | Missing | [backend/app/api](../backend/app/api), [backend/app/main.py](../backend/app/main.py) | No preview or import router exists. |
| CSV validation tests | Missing | [tests/backend](../tests/backend) | No Phase 3 CSV import tests were found. |

## Existing code that supports Phase 3 foundations

### Database and model support

The following components already exist and are relevant to Phase 3:

- [backend/app/models/participant.py](../backend/app/models/participant.py)
  - Declares a `Participant` model.
  - Includes fields for `participant_id`, `status`, `visits_completed`, `visits_planned`, and date fields.
  - Has a unique constraint on `(trial_id, participant_id)`.

- [backend/alembic/versions/9743b997d217_create_initial_schema.py](../backend/alembic/versions/9743b997d217_create_initial_schema.py)
  - Creates the `participants` table and indexes.
  - Contains the database-level uniqueness rule for participant codes within a trial.

- [backend/app/models/trial.py](../backend/app/models/trial.py)
  - Associates `Trial` to `Participant` records via the `participants` relationship.

### Authentication and authorization support

- [backend/app/api/deps.py](../backend/app/api/deps.py)
  - Implements `get_current_user()` and `require_trial_ownership()`.
  - This is the correct enforcement pattern for all trial-scoped CSV endpoints.

- [backend/app/api/trials.py](../backend/app/api/trials.py)
  - The trial router is the correct place to mount participant-scoped subroutes.

### Safety and audit support

- [backend/app/services/audit_service.py](../backend/app/services/audit_service.py)
  - Contains `ACTION_CSV_IMPORT = "csv.import"` and a sanitize routine that strips forbidden key names.
  - This is a good foundation, but it is not yet wired to CSV preview/import operations.

- [backend/app/core/config.py](../backend/app/core/config.py)
  - Defines `MAX_UPLOAD_MB` and `MAX_CSV_ROWS`.
  - This config is necessary but unused at the API layer right now.

## Confirmed missing work for Phase 3

### 1. CSV upload API endpoints are absent

The backend does not define the required endpoints described in [docs/API_SPEC.md](API_SPEC.md):
- `POST /api/trials/{trial_id}/participants/preview`
- `POST /api/trials/{trial_id}/participants/import`

Current app wiring in [backend/app/main.py](../backend/app/main.py) only includes:
- health routes,
- auth router,
- trials router.

No participant/upload router is registered.

### 2. CSV validation is not implemented

The project requirements and acceptance criteria require server-side validation for:
- required headers,
- supported statuses,
- date parsing,
- integer parsing and non-negative constraints,
- negative visit counts,
- duplicate participant codes,
- malformed CSV and row limits.

The current codebase has model fields but no CSV parser or validation service. No code was found in the backend or frontend that checks these conditions.

### 3. Import preview flow is absent

The API contract requires a preview step that validates input and returns a summary without persisting participants. There is no preview response model, no service, and no upload handling code in the repository.

### 4. Import confirmation and atomic writes are absent

The requirements call for an explicit confirmation step and transaction safety. The codebase does not include:
- import-confirmation state,
- transactional insert logic,
- rollback handling,
- per-row rejection tracking,
- a safe failure path that keeps the database unchanged when an import fails.

### 5. Frontend Phase 3 page is still a placeholder

[frontend/src/App.tsx](../frontend/src/App.tsx) still points the `/import` route to a placeholder component instead of a real CSV upload page. There is no upload form, preview table, or confirmation flow.

### 6. No Phase 3 tests exist

The tests folder contains auth, audit, health, authorization, migration, and trial tests, but no CSV preview/import tests. There is no evidence of acceptance coverage for AC-020 through AC-024.

## Proposed implementation plan for Phase 3

### Backend

1. Add a participant CSV API router and register it in [backend/app/main.py](../backend/app/main.py).
2. Implement a CSV validation service with:
   - file-size enforcement using `MAX_UPLOAD_MB`
   - row-count enforcement using `MAX_CSV_ROWS`
   - required header validation (`participant_id`, status, and optional fields)
   - status allowlist: `active`, `completed`, `withdrawn`
   - date parsing for ISO dates
   - integer parsing for `visits_completed` and `visits_planned`
   - negative-value rejection for visit counts
   - duplicate participant detection within the uploaded file and against existing trial data
   - preview summary with `total_rows`, `valid_rows`, `invalid_rows`, `errors`, and limited preview rows
3. Add explicit import confirmation logic.
4. Implement a transaction-scoped import path that writes only after validation passes and records sanitized audit metadata.
5. Use the existing ownership enforcement from [backend/app/api/deps.py](../backend/app/api/deps.py) on every trial-scoped endpoint.

### Frontend

1. Replace the placeholder import page with an authenticated CSV upload form.
2. Handle user flow for:
   - select trial,
   - choose file,
   - upload and preview,
   - display validation issues clearly,
   - require explicit confirmation before import,
   - show loading/error/success states.
3. Integrate with the backend preview and import endpoints using the existing API client pattern in [frontend/src/api/client.ts](../frontend/src/api/client.ts).

### Tests

1. Add backend tests covering:
   - valid CSV preview success,
   - missing required headers,
   - invalid status values,
   - malformed dates,
   - negative visit counts,
   - duplicate participant codes,
   - oversized upload rejection,
   - row count limit rejection,
   - preview without DB writes,
   - atomic import rollback on failure,
   - auth/ownership enforcement on preview and import endpoints,
   - audit metadata sanitization for CSV import events.
2. Add a focused frontend test or build validation for the new upload flow if the project chooses frontend tests later.

## Conclusion

The current codebase already includes the structural foundation for Phase 3:
- participant model,
- database uniqueness constraints,
- auth/ownership enforcement,
- audit sanitization,
- config limits.

However, the actual CSV import and preview workflow required by Phase 3 is not implemented. The missing work is substantial and directly affects the Phase 3 acceptance criteria, especially AC-020 through AC-024.

The confirmed gaps are:
- no CSV preview endpoint,
- no CSV import endpoint,
- no upload validation logic,
- no preview UI,
- no transaction-safe import service,
- no Phase 3 test coverage,
- no implementation of explicit confirmation or database-write safety.

The project is therefore not yet ready for Phase 3 implementation until this audit is reviewed and approved.
