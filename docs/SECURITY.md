# Security and Privacy Requirements

## Data handling
- Use synthetic data for demos, screenshots, and tests.
- Do not upload real identifiable participant data to this portfolio prototype.
- Do not send raw participant rows, identifiers, measurements, or free-text notes to Gemini.
- Minimize stored fields and retain only what the MVP requires.
- Do not claim HIPAA, GDPR, GCP, or other regulatory compliance without a separate qualified assessment and implemented controls.

## Authentication
- Hash passwords with a maintained password-hashing library and appropriate parameters.
- Use HTTPS in deployed environments.
- Keep tokens short-lived and store them using a deliberate strategy. Prefer secure, HttpOnly, SameSite cookies if implementing cookie-based sessions; if bearer tokens are chosen, document the browser storage and XSS trade-offs.
- Apply rate limiting to login and AI endpoints where feasible.
- Avoid verbose auth errors that disclose account existence.

## Authorization
- Every trial-specific backend operation must verify the authenticated user owns or is otherwise authorized for the trial.
- Never rely only on frontend route guards.
- Audit log queries must be scoped by permissions.

## Upload safety
- Enforce file-size and row-count limits.
- Parse CSV as data; do not execute formulas or file contents.
- Sanitize filenames and avoid using client filenames as filesystem paths.
- Validate columns, values, types, statuses, dates, and duplicate IDs on the server.
- Consider spreadsheet formula injection when values may later be exported to CSV; PDF exports should escape text appropriately.

## Secrets and configuration
- Store Gemini API key, database password, and token-signing secret in environment configuration or a deployment secret manager.
- Never commit `.env`, secrets, or production database dumps.
- Rotate any secret that is accidentally exposed.
- Keep `.env.example` free of real values.

## AI safety
- Send the minimum aggregate information required.
- Instruct Gemini not to infer causation, clinical safety, efficacy, or a definitive “healthy/unhealthy” status.
- Do not use LLM output as a source of computed metrics.
- Label output as AI-generated and require human review.
- Do not allow model output to trigger database mutations or participant-level actions.
- Use provider timeouts, bounded input/output, and graceful failure handling.

## Audit logging
Log relevant events but never secrets, passwords, authorization headers, raw participant records, or full sensitive prompts. Define retention and access controls before production use.

## Production readiness
Before any public deployment, review TLS, database network access, backups/restores, monitoring, patching, CORS, rate limits, secrets, data retention, incident response, and applicable privacy/regulatory obligations with qualified personnel.
