import pytest
from app.models import Skill, Evaluation, DriftReport, AuditLog


class TestModels:
    def test_skill_model(self):
        skill = Skill(
            name="test-model",
            display_name="Test Model",
            description="Test model",
            category="evaluation",
            schema="{}",
            is_active=True,
        )
        assert skill.name == "test-model"
        assert skill.display_name == "Test Model"
        assert skill.is_active is True

    def test_evaluation_model(self):
        eval = Evaluation(
            skill_id=1,
            model_name="gpt-4o",
            model_version="2024-08-06",
            provider="openai-compatible",
            sample_size=5,
            status="pending",
        )
        assert eval.model_name == "gpt-4o"
        assert eval.status == "pending"
        assert eval.sample_size == 5

    def test_drift_report_model(self):
        report = DriftReport(
            skill_id=1,
            baseline_model="gpt-4o",
            baseline_version="2024-05-13",
            compare_model="gpt-4o",
            compare_version="2024-08-06",
            regression_detected=False,
            confidence_level=0.95,
            details="{}",
        )
        assert report.regression_detected is False
        assert report.confidence_level == 0.95

    def test_audit_log_model(self):
        log = AuditLog(
            user_id="test-user",
            action="create",
            resource_type="skill",
            resource_id="1",
        )
        assert log.action == "create"
        assert log.resource_type == "skill"