# Data Dictionary

## CSV format
Encoding: UTF-8. Header row required. Date format: ISO `YYYY-MM-DD`. Trim leading/trailing whitespace. Status normalization may be case-insensitive, but accepted canonical values are `active`, `completed`, and `withdrawn`.

### Required fields
| Field | Type | Rules | Example |
|---|---|---|---|
| `participant_id` | string | Required, non-empty, unique within trial, synthetic code only | `SYN-001` |
| `status` | enum string | `active`, `completed`, `withdrawn` | `active` |

### Optional fields
| Field | Type | Rules | Example |
|---|---|---|---|
| `visits_completed` | integer | >= 0 | `3` |
| `visits_planned` | integer | >= 0; if both visit fields supplied, completed <= planned | `8` |
| `enrollment_date` | date | ISO date | `2026-01-15` |
| `last_visit_date` | date | ISO date; validate sensible relationships where possible | `2026-03-01` |
| `next_visit_due_date` | date | ISO date; does not itself prove a missed visit | `2026-03-15` |

Do not include names, emails, phone numbers, addresses, birth dates, medical record numbers, free-text medical notes, or direct identifiers.

## Internal entities
- **User:** account identity and password hash.
- **Trial:** owner, trial code/name/status, start/end dates.
- **Participant:** trial-scoped synthetic participant code, status, optional visit counters/dates.
- **Audit event:** actor, action, entity reference, outcome, timestamp, allowlisted metadata.

## Metric data
- `total_participants`: unique participant records in selected trial.
- `completed_count`: status completed.
- `withdrawn_count`: status withdrawn.
- `active_count`: status active.
- `completion_rate`: completed count / total participants × 100.
- `withdrawal_rate`: withdrawn count / total participants × 100.
- `active_rate`: active count / total participants × 100.
All counts and rates must be computed by backend services.
