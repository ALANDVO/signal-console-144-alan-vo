# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

skeleton-and-core-workflow

## Roadmap

### skeleton-and-core-workflow — FastAPI/React skeleton with core agent skill evaluation workflow

Status: done

Acceptance:
- FastAPI backend with health endpoint and skill evaluation API
- React frontend with skill list and evaluation UI
- Docker compose with backend, frontend, and Keycloak
- Basic CI pipeline running backend/frontend tests
- Portfolio.json with correct metadata
- README with install/run/test instructions

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/exceptions.py`, `backend/app/core/auth.py`, `backend/app/models/__init__.py`, `backend/app/api/__init__.py`, `backend/app/api/schemas.py`, `backend/app/api/routes/health.py`, `backend/app/api/routes/skills.py`, `backend/app/api/routes/drift.py`, `backend/app/api/routes/auth.py`, `backend/app/services/__init__.py`, `backend/tests/test_api.py`, `backend/tests/test_auth.py`, `backend/tests/test_models.py`, `backend/tests/test_services.py`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`, `frontend/src/hooks/useAuth.ts`, `frontend/src/types/api.ts`, `frontend/src/components/Layout.tsx`, `frontend/src/components/LoginPage.tsx`, `frontend/src/components/SkillTable.tsx`, `frontend/src/components/EvaluationTable.tsx`, `frontend/src/components/DriftTable.tsx`, `frontend/src/components/AuditTable.tsx`, `frontend/src/components/SkillTable.test.tsx`, `backend/requirements.txt`, `backend/Dockerfile`, `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/Dockerfile`, `frontend/nginx.conf`, `compose.yaml`, `.github/workflows/ci.yml`, `portfolio.json`, `README.md`, `LICENSE`, `CHANGELOG.md`, `.gitignore`, `.env.example`, `pyproject.toml`, `keycloak/realm-export.json`

Tests: `backend/tests/test_api.py`, `backend/tests/test_auth.py`, `backend/tests/test_models.py`, `backend/tests/test_services.py`, `frontend/src/components/SkillTable.test.tsx`

### skill-evaluation-engine — Substantive domain engine for AI agent skill evaluation

Status: planned

Acceptance:
- Skill registry with schema validation
- Evaluation runner with reproducible baselines
- Drift detection across model versions
- Confidence intervals and statistical reporting

### auth-and-sso — OIDC authentication with Keycloak and SAML broker

Status: planned

Acceptance:
- Keycloak realm import with SAML identity broker
- Backend session management with HttpOnly cookies
- Frontend PKCE flow with in-memory tokens
- Role-based authorization on all data endpoints

### llm-adapters — Multi-provider LLM adapter layer

Status: planned

Acceptance:
- OpenAI-compatible, Anthropic, Gemini, Ollama adapters
- Configurable provider/model/endpoint via environment
- Bounded timeouts and redacted error handling
- Server-side only credential handling

