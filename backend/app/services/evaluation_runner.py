
"""Evaluation runner for executing skill evaluations against LLM providers."""

import json
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Skill, Evaluation
from app.services.llm_adapters import get_llm_adapter, LLMAdapter, LLMResponse
from app.core.exceptions import NotFoundError


@dataclass
class EvaluationResult:
    """Result of a single evaluation trial."""
    trial_index: int
    passed: bool
    score: float
    response: str
    raw_response: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class EvaluationSummary:
    """Aggregated evaluation results."""
    total_trials: int
    passed_trials: int
    mean_score: float
    std_dev: float
    confidence_lower: float
    confidence_upper: float
    passed: bool
    results: List[EvaluationResult]


class EvaluationRunner:
    """Runs skill evaluations against configured LLM provider."""

    def __init__(self, adapter: Optional[LLMAdapter] = None):
        self.adapter = adapter or get_llm_adapter()

    async def run_evaluation(
        self,
        session: AsyncSession,
        evaluation_id: int,
        sample_size: Optional[int] = None,
    ) -> EvaluationSummary:
        """
        Execute an evaluation by running the skill's test cases against the LLM.
        
        Args:
            session: Database session
            evaluation_id: ID of evaluation to run
            sample_size: Optional override for number of trials
            
        Returns:
            EvaluationSummary with aggregated results
        """
        # Get evaluation and skill
        eval_result = await session.execute(select(Evaluation).where(Evaluation.id == evaluation_id))
        evaluation = eval_result.scalar_one_or_none()
        if not evaluation:
            raise NotFoundError("Evaluation", str(evaluation_id))

        skill_result = await session.execute(select(Skill).where(Skill.id == evaluation.skill_id))
        skill = skill_result.scalar_one_or_none()
        if not skill:
            raise NotFoundError("Skill", str(evaluation.skill_id))

        # Check if adapter is available
        if not self.adapter:
            # No LLM configured - mark as failed with helpful message
            from app.services import update_evaluation_status
            await update_evaluation_status(
                session,
                evaluation_id,
                "failed",
                error_message="No LLM provider configured. Set LLM_API_KEY and LLM_PROVIDER environment variables.",
            )
            raise RuntimeError("No LLM provider configured")

        # Parse skill schema for test cases
        try:
            skill_schema = json.loads(skill.schema)
        except json.JSONDecodeError:
            from app.services import update_evaluation_status
            await update_evaluation_status(
                session,
                evaluation_id,
                "failed",
                error_message="Invalid skill schema JSON",
            )
            raise RuntimeError("Invalid skill schema JSON")

        test_cases = skill_schema.get("test_cases", [])
        if not test_cases:
            from app.services import update_evaluation_status
            await update_evaluation_status(
                session,
                evaluation_id,
                "failed",
                error_message="Skill schema missing test_cases array",
            )
            raise RuntimeError("Skill schema missing test_cases array")

        # Determine actual sample size
        n_trials = sample_size or evaluation.sample_size
        if n_trials > len(test_cases):
            n_trials = len(test_cases)

        # Update status to running
        from app.services import update_evaluation_status
        await update_evaluation_status(session, evaluation_id, "running")

        # Run trials
        results = []
        for i in range(n_trials):
            test_case = test_cases[i]
            result = await self._run_single_trial(skill, test_case, i)
            results.append(result)

        # Aggregate results
        summary = self._aggregate_results(results)

        # Update evaluation with results
        await update_evaluation_status(
            session,
            evaluation_id,
            "completed",
            score=summary.mean_score,
            confidence_lower=summary.confidence_lower,
            confidence_upper=summary.confidence_upper,
            passed=summary.passed,
            metadata=json.dumps({
                "results": [
                    {
                        "trial_index": r.trial_index,
                        "passed": r.passed,
                        "score": r.score,
                        "response": r.response,
                        "error": r.error,
                    }
                    for r in results
                ],
                "model_name": evaluation.model_name,
                "model_version": evaluation.model_version,
                "provider": evaluation.provider,
            }),
        )

        return summary

    async def _run_single_trial(
        self,
        skill: Skill,
        test_case: Dict[str, Any],
        trial_index: int,
    ) -> EvaluationResult:
        """Run a single evaluation trial."""
        prompt = test_case.get("input", "")
        expected = test_case.get("expected_output", "")
        evaluation_type = test_case.get("evaluation_type", "exact_match")
        threshold = test_case.get("threshold", 0.8)

        try:
            # Build system prompt from skill description
            system_prompt = (
                f"You are evaluating the skill: {skill.display_name}. "
                f"Description: {skill.description}. "
                f"Category: {skill.category}. "
                f"Follow the instructions precisely."
            )

            # Get response from LLM
            response = await self.adapter.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.0,
            )

            # Evaluate response
            passed, score = self._evaluate_response(
                response.content,
                expected,
                evaluation_type,
                threshold,
            )

            return EvaluationResult(
                trial_index=trial_index,
                passed=passed,
                score=score,
                response=response.content,
                raw_response=response.raw_response,
            )

        except Exception as e:
            return EvaluationResult(
                trial_index=trial_index,
                passed=False,
                score=0.0,
                response="",
                raw_response={},
                error=str(e),
            )

    def _evaluate_response(
        self,
        response: str,
        expected: str,
        evaluation_type: str,
        threshold: float,
    ) -> tuple[bool, float]:
        """Evaluate a single response against expected output."""
        if evaluation_type == "exact_match":
            passed = response.strip() == expected.strip()
            score = 1.0 if passed else 0.0
        elif evaluation_type == "contains":
            passed = expected.lower() in response.lower()
            score = 1.0 if passed else 0.0
        elif evaluation_type == "json_match":
            try:
                resp_json = json.loads(response)
                exp_json = json.loads(expected)
                passed = resp_json == exp_json
                score = 1.0 if passed else 0.0
            except json.JSONDecodeError:
                passed = False
                score = 0.0
        elif evaluation_type == "semantic_similarity":
            # Simple word overlap as proxy for semantic similarity
            resp_words = set(response.lower().split())
            exp_words = set(expected.lower().split())
            if not exp_words:
                score = 0.0
            else:
                overlap = len(resp_words & exp_words) / len(exp_words)
                score = overlap
            passed = score >= threshold
        else:
            # Default to exact match
            passed = response.strip() == expected.strip()
            score = 1.0 if passed else 0.0

        return passed, score

    def _aggregate_results(self, results: List[EvaluationResult]) -> EvaluationSummary:
        """Aggregate trial results into summary statistics."""
        if not results:
            return EvaluationSummary(
                total_trials=0,
                passed_trials=0,
                mean_score=0.0,
                std_dev=0.0,
                confidence_lower=0.0,
                confidence_upper=0.0,
                passed=False,
                results=[],
            )

        total = len(results)
        passed_count = sum(1 for r in results if r.passed)
        scores = [r.score for r in results]
        mean_score = sum(scores) / total if total > 0 else 0.0

        # Standard deviation
        if total > 1:
            variance = sum((s - mean_score) ** 2 for s in scores) / (total - 1)
            std_dev = variance ** 0.5
        else:
            std_dev = 0.0

        # 95% confidence interval (using t-distribution approximation)
        # For small samples, use z=1.96 as approximation
        z = 1.96
        margin = z * (std_dev / (total ** 0.5)) if total > 0 else 0.0
        confidence_lower = max(0.0, mean_score - margin)
        confidence_upper = min(1.0, mean_score + margin)

        # Overall pass: majority of trials passed AND mean score >= 0.5
        overall_passed = (passed_count > total / 2) and (mean_score >= 0.5)

        return EvaluationSummary(
            total_trials=total,
            passed_trials=passed_count,
            mean_score=mean_score,
            std_dev=std_dev,
            confidence_lower=confidence_lower,
            confidence_upper=confidence_upper,
            passed=overall_passed,
            results=results,
        )


async def run_evaluation_background(
    evaluation_id: int,
) -> None:
    """
    Background task to run an evaluation.
    This creates its own database session.
    """
    from app.core.database import get_session
    
    async with get_session() as session:
        runner = EvaluationRunner()
        try:
            await runner.run_evaluation(session, evaluation_id)
        except Exception:
            # Error already handled in run_evaluation
            pass

