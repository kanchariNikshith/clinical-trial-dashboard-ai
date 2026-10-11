# Test Plan

## Test principles
Use synthetic fixtures only. Keep unit tests deterministic. Mock Gemini in regular automated tests; keep any live-provider test opt-in and never required for the default test suite.

## Backend unit tests
- Metric counts/rates for mixed statuses, empty data, and rounding.
- CSV parser: required columns, blank cells, invalid statuses, malformed dates, negative integers, oversized input, duplicate IDs.
- Password hashing and token expiry/validation.
- AI prompt builder includes aggregate metrics and excludes participant-level identifiers.
- PDF service includes expected headings/disclaimer and uses the same metric values.

## API integration tests
- Health endpoint.
- Register/login/current-user/logout behavior as implemented.
- Trial CRUD and duplicate trial code.
- Authorization boundaries between two users.
- CSV preview does not persist data.
- CSV import persists only after confirmation and rolls back on failure.
- Metrics endpoint agrees with persisted test data.
- AI endpoint handles success, missing key, timeout, quota/provider error, and malformed response.
- PDF endpoint returns `application/pdf` and denies unauthorized access.
- Audit endpoint access and filtering.

## Frontend tests
- Login validation and failure states.
- Trial list/create states.
- CSV upload preview, validation error rendering, confirmation, and import result.
- KPI cards and chart labels for normal and empty data.
- AI loading/success/failure/unconfigured states and disclaimer.
- PDF download action and error handling.
- Protected route behavior and sign-out.
- Responsive smoke checks at mobile, tablet, and desktop widths.

## Security-oriented tests
- Requests without credentials.
- Cross-user trial ID substitution.
- Malicious filenames and malformed CSV content.
- Oversized uploads and row-limit enforcement.
- XSS-like text in CSV values and AI response rendered as text.
- Secret redaction in logs and error responses.
- CORS rejects unapproved origins.
- Rate limiting for login/AI where implemented.

## Sample metric fixture
120 synthetic participants:
- completed: 95
- withdrawn: 15
- active: 10
Expected:
- completion rate = 95 / 120 × 100 = 79.166...% (display 79.17%)
- withdrawal rate = 15 / 120 × 100 = 12.5%
- active rate = 10 / 120 × 100 = 8.333...% (display 8.33%)

## Exit criteria
- All critical tests pass.
- Known unrelated failures are recorded, not hidden.
- No test uses real participant-identifiable information.
- Frontend lint/type checks and backend lint/type checks (if configured) pass.
- At least one end-to-end happy path is verified: login → create trial → preview/import CSV → dashboard metrics → AI insight (mocked if needed) → PDF export.
