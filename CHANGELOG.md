# Changelog

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

### Added
- LLM adapter layer supporting OpenAI-compatible, Anthropic, Gemini, and Ollama providers
- Evaluation runner with statistical aggregation (mean score, standard deviation, 95% confidence intervals)
- POST /api/v1/skills/evaluations/{id}/run endpoint for background evaluation execution
- Evaluation trial evaluation types: exact_match, contains, json_match, semantic_similarity
- Test for evaluation run endpoint

### Changed
- Updated feature-plan.json: skill-evaluation-engine and llm-adapters now in_progress
- Updated PLAN.md with implementation paths for in-progress features
- Updated STATUS.md with checkpoint summary and outstanding findings

### Verified
- All 42 backend tests pass
- All 3 frontend tests pass

### Known Limitations
- Evaluation runner requires LLM_API_KEY environment variable for actual LLM calls
- Background task uses separate database session; test waits for completion

## 1.1.0 — work-in-progress checkpoint

---

Alan Vo · [alanvo.net](https://alanvo.net) · [X: @alanvoasi](https://x.com/alanvoasi)
