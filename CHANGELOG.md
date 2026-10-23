# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-23

### Added
- Initial release of Signal Console
- FastAPI backend with health checks, skills, evaluations, drift detection, and audit logging
- React + TypeScript + Vite frontend with skill management, evaluation runner, drift reports, and audit logs
- OIDC authentication with Keycloak integration and SAML identity broker
- Role-based access control (Admin, Operator, Analyst, Viewer)
- Multi-provider LLM adapter layer (OpenAI-compatible, Anthropic, Gemini, Ollama)
- SQLite persistent storage with SQLAlchemy
- Docker Compose with backend, frontend, and Keycloak services
- Demo mode for local development
- Comprehensive API documentation and OpenAPI schema
- Portfolio.json with project metadata
- CI/CD pipeline with backend and frontend tests

### Security
- HttpOnly, SameSite cookies for session management
- CSRF protection on state-changing operations
- PKCE for OIDC authorization code flow
- Nonce validation for ID tokens
- Signature, issuer, and audience validation for OIDC tokens
- Role-based authorization on all data endpoints
- No hardcoded secrets or credentials
- Audit logging for all authenticated actions

### AI/ML Evaluation
- Skill evaluation framework with reproducible baselines
- Configurable sample sizes and confidence intervals
- Drift detection with effect size and p-value calculation
- Multi-provider evaluation support
- Deterministic offline core (works without LLM keys)

## [Unreleased]

### Planned
- Automated evaluation scheduler
- Webhook notifications for evaluation completion
- Advanced drift visualization charts
- Skill template marketplace
- Integration with Driftproof evaluation suites
- Prometheus metrics export
- PostgreSQL production database support