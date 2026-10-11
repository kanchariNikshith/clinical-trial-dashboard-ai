# Clinical Trial Dashboard with AI Insights

A portfolio-oriented full-stack application for uploading **synthetic or appropriately de-identified** clinical-trial participant data, viewing operational metrics, generating AI-assisted summaries with Google Gemini, and exporting PDF reports.

> **Important scope boundary:** This is an educational/operational analytics prototype, not a validated clinical system, electronic data capture (EDC) system, medical device, or substitute for clinical/statistical review. Do not upload real patient-identifiable data. AI output must be reviewed by a qualified human before use in decisions.

## MVP features
- User registration/login and authenticated API access
- Create and view trials
- CSV upload with schema validation, preview, and bulk participant import
- Trial metrics and interactive charts
- AI-assisted narrative insights using Google Gemini
- PDF report export
- Audit log for security-relevant and data-changing actions
- API documentation via FastAPI OpenAPI/Swagger UI
- Docker-based local development

## Technology
- Frontend: React + TypeScript + Vite
- UI/data visualization: responsive CSS (or chosen UI library) and Recharts
- Backend: Python + FastAPI + Pydantic
- Persistence: PostgreSQL + SQLAlchemy 2.x + Alembic
- Authentication: password hashing and short-lived signed access tokens; secure token handling
- AI: Google Gen AI SDK (`google-genai`) with Gemini model selected through environment configuration
- Data processing: Pandas
- PDF: ReportLab
- Tests: pytest, HTTPX, and frontend test tooling
- Packaging: Docker Compose

## Documentation
- [Requirements](docs/PROJECT_REQUIREMENTS.md)
- [UI/UX specification](docs/UI_UX_SPEC.md)
- [Technology stack](docs/TECH_STACK.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Database schema](docs/DATABASE_SCHEMA.md)
- [API specification](docs/API_SPEC.md)
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Acceptance criteria](docs/ACCEPTANCE_CRITERIA.md)
- [Test plan](docs/TEST_PLAN.md)
- [Data dictionary](docs/DATA_DICTIONARY.md)
- [Security](docs/SECURITY.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Environment template](.env.example)

## Prerequisites
- Git
- Docker Desktop / Docker Engine with Docker Compose (recommended)
- Google Gemini API key for AI features; core dashboard should remain usable if AI is not configured
- A modern browser

## Local setup

### Option A: Direct Local Development (No Docker Required)
1. Backend setup:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # On Windows (or source .venv/bin/activate on Unix)
   pip install -r backend/requirements.txt
   uvicorn backend.app.main:app --port 8000 --reload
   ```
2. Frontend setup:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
3. Run automated tests:
   ```bash
   .venv\Scripts\pytest
   cd frontend && npm run build
   ```
4. Access applications:
   - Frontend: `http://localhost:5173`
   - FastAPI Docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

### Option B: Docker Compose (When Docker is installed)
1. Copy `.env.example` to `.env`.
2. Set strong local-only secrets and optional Gemini API key in `.env`. Never commit `.env`.
3. Run `docker compose up --build`.
4. Open the frontend at `http://localhost:5173` and API docs at `http://localhost:8000/docs`.


## Sample CSV
A starter CSV should use synthetic records and the schema defined in `docs/DATA_DICTIONARY.md`. Include no real names, emails, dates of birth, medical record numbers, or other direct identifiers.

## Development principles
- Build in phases; do not implement all features in one uncontrolled change.
- Validate inputs on the backend even when frontend validation exists.
- Never send participant-level rows or direct identifiers to the AI provider. Send only the minimum aggregated metrics needed for the requested insight.
- AI output is advisory, must state its limitations, and must not fabricate follow-up actions or completion predictions.
- Keep audit logs free of passwords, tokens, API keys, and unnecessary sensitive data.
- Add tests and update documentation as behavior changes.
