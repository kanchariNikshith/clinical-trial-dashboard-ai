# Project Requirements

## 1. Overview
**Name:** Clinical Trial Dashboard with AI Insights
**Type:** Full-stack web application / portfolio MVP
**Primary users:** Researchers, trial coordinators, and authorized demo users
**Purpose:** Help users import participant-status data, view transparent operational metrics, ask for an AI-assisted summary of aggregated trial metrics, and export a PDF report.

## 2. Problem statement
Trial status information may be stored in CSV files and can be difficult to summarize consistently. This application provides a single dashboard for validated status counts and simple visualizations, with optional AI-generated explanations of the aggregated results.

## 3. Scope and safety boundary
This MVP is for demonstration and operational analytics using synthetic or appropriately de-identified data. It is not a validated clinical trial management/EDC system, does not establish clinical efficacy or safety, and must not be used as the sole basis for participant care, trial decisions, regulatory submissions, or safety reporting. Do not upload direct identifiers or sensitive participant-level health records.

## 4. User roles
- **Authenticated user:** can create/view trials they are authorized to access, upload CSVs, view metrics, request AI summaries, export reports, and review permitted audit events.
- **Administrator (optional if implemented in MVP):** can manage users and review broader audit events.
Default recommendation: implement a single authenticated user role with per-user trial ownership for MVP; keep role-based admin capabilities out of scope unless explicitly approved.

## 5. Functional requirements
- **FR-001 Authentication:** Users can register/sign in and sign out. Protected APIs reject unauthenticated requests.
- **FR-002 Trial management:** An authenticated user can create a trial with unique trial code, name, status, start date, and optional end date.
- **FR-003 CSV upload:** User selects a trial and uploads a CSV. The UI previews parsed data and validation errors before import.
- **FR-004 Validation:** Backend validates file size, row limit, required columns, field types, allowed status values, and duplicate participant IDs within a trial.
- **FR-005 Bulk import:** Valid rows are imported transactionally; invalid rows are reported clearly. Default behavior: reject the entire import if required structural validation fails; row-level errors should be previewed before user confirms import.
- **FR-006 Metrics:** Dashboard displays total participants, completed, withdrawn, active, completion rate, and withdrawal rate with denominators defined below.
- **FR-007 Charts:** Show participant status breakdown and a time-based trend only when sufficient date data exists.
- **FR-008 AI insight:** User can request a Gemini-generated narrative based on aggregated metrics and available aggregate trends only.
- **FR-009 AI failure handling:** If AI configuration is absent, provider times out, or request fails, the core dashboard continues working and displays a useful message.
- **FR-010 PDF export:** User can download a PDF containing trial metadata, metrics, charts or chart summaries, generation time, and any AI insight with an explicit AI advisory disclaimer.
- **FR-011 Audit log:** Record security-relevant and important actions such as login success/failure, trial creation, upload/import, AI analysis request, and PDF export. Do not log secrets or raw participant rows.
- **FR-012 API docs:** FastAPI exposes OpenAPI docs in development.
- **FR-013 Health check:** `GET /health` returns service health without exposing secrets.
- **FR-014 Authorization:** Users can access only trials and records they are authorized to access.
- **FR-015 Data export correctness:** Report values must match server-computed metrics for the selected trial and selected reporting time.

## 6. Metric definitions
For a selected trial:
- `total_participants` = count of unique imported participant records for that trial.
- `completed_count` = participants whose normalized status is `completed`.
- `withdrawn_count` = participants whose normalized status is `withdrawn`.
- `active_count` = participants whose normalized status is `active`.
- `completion_rate` = `completed_count / total_participants * 100`; this is the proportion of all enrolled records marked completed, not a survival estimate.
- `withdrawal_rate` = `withdrawn_count / total_participants * 100`.
- Rates are `0` when the denominator is zero and the UI must show that no participants are available rather than implying a meaningful rate.
- Status counts should reconcile to total only if every record has exactly one supported status. Unknown/missing statuses must be rejected or explicitly reported rather than silently omitted.
- Example only: 120 total, 95 completed, 15 withdrawn, 10 active yields completion 79.17%, withdrawal 12.50%, active 8.33%. These are illustrative synthetic figures, not evidence of trial health.

## 7. CSV input
Required columns:
- `participant_id` (synthetic/study-specific code; unique within a trial)
- `status` (`active`, `completed`, `withdrawn`)
Optional columns:
- `visits_completed` (non-negative integer)
- `visits_planned` (non-negative integer, >= visits_completed when both known)
- `enrollment_date` (ISO date `YYYY-MM-DD`)
- `last_visit_date` (ISO date)
- `next_visit_due_date` (ISO date; optional and not proof that a visit was missed)
- `measurement_date`, `measurement_type`, `measurement_value` should be added only if measurement support is deliberately implemented.
Do not include participant names, email addresses, date of birth, medical record numbers, or other direct identifiers.

## 8. AI behavior
- Send only minimized aggregate values and approved aggregate trends to Gemini.
- Ask for descriptive, cautious interpretation and data-quality observations, not medical advice.
- The model must distinguish observed values from possible explanations.
- It must not invent a benchmark for “healthy,” “low dropout,” a follow-up need, or a projected completion date.
- Follow-up flags can only be produced by a deterministic, documented rule using an available `next_visit_due_date` and a defined as-of date; label them as operational flags requiring coordinator review.
- Completion-date projection is out of MVP unless a transparent, validated calculation method and sufficient schedule data are added. Do not ask the LLM to guess a date.
- Every insight displays: AI-generated, based on the available aggregate data, not a clinical conclusion, human review required.

## 9. Non-functional requirements
- Security: password hashing, authorization, secret management, upload limits, safe errors, audit logging.
- Reliability: transactional imports and graceful AI-provider failure.
- Performance: target dashboard response under 2 seconds for a typical demo dataset up to 10,000 participants on a local development machine; treat this as a target to test, not a guarantee.
- Usability: clear validation feedback and accessible chart labels.
- Maintainability: layered backend, typed frontend, migrations, automated tests, documented setup.
- Privacy: no real identifiable participant data in demo or test fixtures.

## 10. MVP exclusions
- Clinical decision support, safety signal detection, medical recommendations, or trial efficacy conclusions.
- Real EHR/EDC integration.
- Real participant identifiable data.
- Regulatory compliance certification or claims of HIPAA/GDPR compliance.
- Statistical survival analysis or validated completion prediction.
- Multi-tenant enterprise administration and complex permission matrix.
- Production deployment until secrets, database security, TLS, backups, monitoring, and privacy review are addressed.

## 11. Assumptions and open decisions
Assumptions:
- React + TypeScript frontend and FastAPI backend.
- PostgreSQL is the primary persistent database.
- Gemini API is optional and configured by environment variable.
- One participant has one status per trial in this MVP.
- CSV imports are associated with an existing trial.

Open decisions requiring approval:
- Whether user registration is public or users are provisioned by an administrator.
- Whether duplicate participant IDs should be rejected or updated on later uploads. Recommended MVP: reject duplicates and never silently overwrite.
- Whether admin role is required for first release. Recommended: defer.
- Exact hosting provider and production budget. Recommended: keep deployment provider-neutral initially.
