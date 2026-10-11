# Deployment and Local Development

## Local development (recommended: Docker Compose)
Prerequisites:
- Git
- Docker Desktop or Docker Engine with Compose
- Gemini API key only for live AI functionality

Steps:
1. Clone/open the repository.
2. Copy `.env.example` to `.env`.
3. Replace local placeholder secrets with strong random values.
4. Set `GEMINI_API_KEY` only if enabling AI.
5. Build and start services using `docker compose up --build`.
6. Apply Alembic migrations using the command documented by the backend setup.
7. Open the frontend and FastAPI `/docs` endpoints.
8. Run backend and frontend tests using the commands in the final README.

The exact commands, service names, and ports must be kept synchronized with actual Dockerfiles and Compose configuration.

## Environment variables
- `DATABASE_URL`: PostgreSQL connection string.
- `JWT_SECRET_KEY`: strong secret for signing tokens, if JWT is selected.
- `GEMINI_API_KEY`: Google Gemini key; optional for core app.
- `GEMINI_MODEL`: supported model identifier.
- `CORS_ORIGINS`: allowed frontend origins.
- `MAX_UPLOAD_MB`, `MAX_CSV_ROWS`: server-side upload limits.
- `APP_ENV`, `LOG_LEVEL`: environment and logging settings.

## Production considerations
Do not deploy publicly until:
- HTTPS/TLS is configured.
- Secrets are stored in the hosting provider's secret manager.
- Database access is private and credentials are least-privilege.
- Migrations are run through a controlled release process.
- Backups and restore procedure are tested.
- Health checks, monitoring, and error reporting are configured.
- CORS, rate limits, upload limits, and authentication are reviewed.
- Privacy, data retention, and regulatory obligations are assessed.
- No real participant data is used without appropriate approvals and safeguards.

## Provider choice
Hosting provider is intentionally undecided. Render, Railway, Fly.io, AWS, or Azure may be evaluated later based on current pricing, region, database support, and deployment needs. Do not assume free tiers or current prices without checking at deployment time.
