# Technology Stack

## Approved baseline
| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React + TypeScript + Vite | Responsive single-page application |
| Routing | React Router | Page navigation and protected routes |
| Server state/API | Fetch wrapper or Axios; TanStack Query optional | API calls, loading/error/cache handling |
| Charts | Recharts | Status and trend charts |
| Styling | CSS modules or a consistent utility/UI system | Responsive, reusable design |
| Backend | Python 3.11+ (or a compatible supported version) + FastAPI | REST API |
| Validation | Pydantic | Request/response validation |
| Database | PostgreSQL | Persistent trial and participant data |
| ORM/migrations | SQLAlchemy 2.x + Alembic | Data access and schema evolution |
| CSV processing | Pandas plus Python CSV validation | Parse and validate uploads |
| AI | `google-genai` SDK | Google Gemini API integration |
| PDF | ReportLab | Server-generated PDF reports |
| Auth | Secure password hashing library + signed access tokens | Login and protected endpoints |
| Tests | pytest, HTTPX; frontend test runner | Automated testing |
| Packaging | Docker + Docker Compose | Reproducible local environment |

## Gemini integration correction
Use Google's official `google-genai` Python SDK for Gemini, not the OpenAI SDK. Keep the model ID configurable via `GEMINI_MODEL`; confirm a currently supported model name and API access during implementation rather than hardcoding an assumed model. Gemini API access, quotas, and free-tier conditions can change.

## Design constraints
- AI provider must be behind a service interface so it can be disabled or replaced without rewriting domain logic.
- Dashboard metrics are computed deterministically in backend code, not by the LLM.
- The AI service receives aggregated metrics only.
- Core CSV import, dashboard, and PDF export should work if the AI key is absent, except the AI-specific action.
- Use dependency versions compatible with the selected Python/Node versions and pin reproducible versions in lockfiles/manifests.

## Suggested repository layout
```text
clinical-trial-dashboard/
├── AGENTS.md
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── features/
│   │   ├── pages/
│   │   ├── types/
│   │   └── main.tsx
│   └── ...
├── backend/
│   ├── pyproject.toml or requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── ...
│   └── alembic/
├── tests/
│   ├── backend/
│   └── frontend/
└── docs/
```

## Version and dependency policy
Choose currently supported compatible versions during implementation. Do not use floating production dependencies without a lockfile. Avoid adding libraries when the standard library or existing stack is sufficient. Document any deviation from this stack and explain the reason.
