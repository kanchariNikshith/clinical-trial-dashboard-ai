# API Specification

Base path: `/api`. JSON responses use consistent error structures. Exact schemas should be implemented in Pydantic and reflected in FastAPI OpenAPI docs. All trial-scoped endpoints require authentication and authorization.

## Health
### `GET /health`
Public liveness check. Response:
```json
{"status": "healthy"}
```
Do not expose environment variables, database credentials, or internal exception details.

## Authentication
### `POST /api/auth/register`
Only if public registration is approved. Accept email and password; validate and hash password. Return safe user profile and access token or use a documented secure session strategy.

### `POST /api/auth/login`
Accept credentials; return access token/session. Use generic failure message for invalid credentials.

### `POST /api/auth/logout`
Invalidate session/refresh token if the selected token design supports server-side invalidation. If using stateless short-lived tokens only, document the actual logout behavior rather than pretending tokens are revoked.

### `GET /api/auth/me`
Return the current authenticated user's safe profile.

## Trials
### `GET /api/trials`
List only trials the current user may access.

### `POST /api/trials`
Create trial. Example request:
```json
{
  "trial_code": "DEMO-001",
  "trial_name": "Synthetic Trial Demo",
  "status": "active",
  "start_date": "2026-01-01",
  "end_date": null
}
```

### `GET /api/trials/{trial_id}`
Return trial metadata after authorization.

## CSV upload
### `POST /api/trials/{trial_id}/participants/preview`
Multipart upload. Validate CSV and return preview without persisting participants.
Example response:
```json
{
  "total_rows": 120,
  "valid_rows": 120,
  "invalid_rows": 0,
  "errors": [],
  "preview": [
    {"participant_id": "SYN-001", "status": "active"}
  ]
}
```
Preview must be limited; do not return every row for large files.

### `POST /api/trials/{trial_id}/participants/import`
Import a validated upload after explicit user confirmation. Implementation may accept the file again or use a short-lived server-side preview token; choose and document one secure design. Revalidate on the server. Do not trust a client-supplied preview as proof of validity.

## Metrics
### `GET /api/trials/{trial_id}/metrics`
Example response:
```json
{
  "trial_id": "example-id",
  "total_participants": 120,
  "completed_count": 95,
  "withdrawn_count": 15,
  "active_count": 10,
  "completion_rate": 79.17,
  "withdrawal_rate": 12.5,
  "active_rate": 8.33,
  "data_quality": {"status_counts_reconcile": true},
  "definitions": {
    "completion_rate": "completed_count / total_participants * 100",
    "withdrawal_rate": "withdrawn_count / total_participants * 100"
  }
}
```
Values above are synthetic examples. The API must compute the values from persisted records and return consistent denominators.

## AI insights
### `POST /api/trials/{trial_id}/ai-analysis`
Use POST because the operation invokes an external provider and may be audited. Request may contain a narrowly defined analysis question, but the backend must not accept arbitrary raw participant data for the prompt. Backend computes metrics and constructs the AI input.
Example response:
```json
{
  "analysis": "AI-generated narrative...",
  "model": "configured-model-id",
  "generated_at": "2026-01-01T12:00:00Z",
  "disclaimer": "AI-generated operational summary; review independently. Not a clinical conclusion."
}
```
If Gemini is unconfigured, return a documented service-unavailable response while dashboard metrics remain available.

## PDF report
### `GET /api/trials/{trial_id}/report.pdf`
Return `application/pdf` with attachment filename. Verify access and generate from backend metrics. Include the AI insight only if requested/available and clearly label it.

## Audit log
### `GET /api/audit-events`
Return only events the current user is permitted to view. Use pagination and allowlisted filters. Do not expose other users' audit records without explicit admin authorization.

## Error response convention
Recommended shape:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The uploaded CSV has invalid rows.",
    "details": []
  }
}
```
Use appropriate HTTP status codes: 400 malformed input, 401 unauthenticated, 403 forbidden, 404 not found, 409 conflict/duplicate, 413 upload too large, 422 schema validation, 429 provider/rate limit where appropriate, 503 optional AI service unavailable, and 500 generic internal error. Never return stack traces to clients.

## OpenAPI
FastAPI generates `/docs` and `/openapi.json` in development. Restrict or disable interactive docs in production if appropriate for the deployment.
