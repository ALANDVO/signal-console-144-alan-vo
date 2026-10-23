import pytest
from httpx import AsyncClient


class TestHealth:
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert "version" in data
        assert "environment" in data

    async def test_readiness_check(self, client: AsyncClient):
        response = await client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data

    async def test_liveness_check(self, client: AsyncClient):
        response = await client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"


class TestAuth:
    async def test_demo_login(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/demo-login")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "demo-user"
        assert "viewer" in data["roles"]
        assert "analyst" in data["roles"]
        assert "operator" in data["roles"]
        # Check cookie set
        assert "session=" in response.headers.get("set-cookie", "")

    async def test_get_current_user_after_demo_login(self, client: AsyncClient):
        await client.get("/api/v1/auth/demo-login")
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "demo-user"

    async def test_logout(self, client: AsyncClient):
        await client.get("/api/v1/auth/demo-login")
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        # Cookie should be cleared
        assert 'session=""' in response.headers.get("set-cookie", "")

    async def test_unauthorized_without_login(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401


class TestSkills:
    async def test_create_skill_unauthorized(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/skills",
            json={
                "name": "test-skill",
                "display_name": "Test Skill",
                "description": "A test skill",
                "category": "evaluation",
                "schema": "{}",
            },
        )
        assert response.status_code == 401

    async def test_create_skill_as_operator(self, demo_user_client):
        client, cookie = demo_user_client
        client.headers["Cookie"] = cookie
        
        response = await client.post(
            "/api/v1/skills",
            json={
                "name": "code-review",
                "display_name": "Code Review",
                "description": "Reviews code quality and suggests improvements",
                "category": "quality",
                "schema": '{"type": "object", "properties": {"threshold": {"type": "number"}}}',
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "code-review"
        assert data["display_name"] == "Code Review"
        assert data["category"] == "quality"
        assert data["is_active"] is True

    async def test_list_skills(self, demo_user_client):
        client, cookie = demo_user_client
        client.headers["Cookie"] = cookie
        
        # Create a skill first
        await client.post(
            "/api/v1/skills",
            json={
                "name": "test-skill-1",
                "display_name": "Test Skill 1",
                "description": "A test skill",
                "category": "evaluation",
                "schema": "{}",
            },
        )
        
        response = await client.get("/api/v1/skills")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    async def test_get_skill_by_id(self, demo_user_client):
        client, cookie = demo_user_client
        client.headers["Cookie"] = cookie
        
        create_resp = await client.post(
            "/api/v1/skills",
            json={
                "name": "get-by-id-test",
                "display_name": "Get By ID Test",
                "description": "Test skill",
                "category": "evaluation",
                "schema": "{}",
            },
        )
        skill_id = create_resp.json()["id"]
        
        response = await client.get(f"/api/v1/skills/{skill_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == skill_id
        assert data["name"] == "get-by-id-test"

    async def test_get_skill_by_name(self, demo_user_client):
        client, cookie = demo_user_client
        client.headers["Cookie"] = cookie
        
        await client.post(
            "/api/v1/skills",
            json={
                "name": "get-by-name-test",
                "display_name": "Get By Name Test",
                "description": "Test skill",
                "category": "evaluation",
                "schema": "{}",
            },
        )
        
        response = await client.get("/api/v1/skills/by-name/get-by-name-test")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "get-by-name-test"

    async def test_update_skill(self, demo_user_client):
        client, cookie = demo_user_client
        client.headers["Cookie"] = cookie
        
        create_resp = await client.post(
            "/api/v1/skills",
            json={
                "name": "update-test",
                "display_name": "Update Test",
                "description": "Test skill",
                "category": "evaluation",
                "schema": "{}",
            },
        )
        skill_id = create_resp.json()["id"]
        
        response = await client.patch(
            f"/api/v1/skills/{skill_id}",
            json={"display_name": "Updated Name", "description": "Updated description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Name"
        assert data["description"] == "Updated description"

    async def test_delete_skill_forbidden_for_operator(self, demo_user_client):
        client, cookie = demo_user_client
        client.headers["Cookie"] = cookie
        
        create_resp = await client.post(
            "/api/v1/skills",
            json={
                "name": "delete-test",
                "display_name": "Delete Test",
                "description": "Test skill",
                "category": "evaluation",
                "schema": "{}",
            },
        )
        skill_id = create_resp.json()["id"]
        
        response = await client.delete(f"/api/v1/skills/{skill_id}")
        # Operator should not be able to delete (admin only)
        assert response.status_code == 403

    async def test_duplicate_skill_name(self, demo_user_client):
        client, cookie = demo_user_client
        client.headers["Cookie"] = cookie
        
        await client.post(
            "/api/v1/skills",
            json={
                "name": "duplicate-test",
                "display_name": "Duplicate Test",
                "description": "Test skill",
                "category": "evaluation",
                "schema": "{}",
            },
        )
        
        response = await client.post(
            "/api/v1/skills",
            json={
                "name": "duplicate-test",
                "display_name": "Duplicate Test 2",
                "description": "Test skill 2",
                "category": "evaluation",
                "schema": "{}",
            },
        )
        assert response.status_code == 409


class TestEvaluations:
    async def test_create_evaluation(self, demo_user_client):
        client, cookie = demo_user_client
        client.headers["Cookie"] = cookie
        
        # Create skill first
        skill_resp = await client.post(
            "/api/v1/skills",
            json={
                "name": "eval-test-skill",
                "display_name": "Eval Test Skill",
                "description": "Skill for evaluation testing",
                "category": "evaluation",
                "schema": "{}",
            },
        )
        skill_id = skill_resp.json()["id"]
        
        # Create evaluation
        response = await client.post(
            f"/api/v1/skills/{skill_id}/evaluate",
            json={
                "skill_id": skill_id,
                "model_name": "gpt-4o",
                "model_version": "2024-08-06",
                "provider": "openai-compatible",
                "sample_size": 5,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["skill_id"] == skill_id
        assert data["model_name"] == "gpt-4o"
        assert data["status"] == "pending"

    async def test_list_evaluations(self, demo_user_client):
        client, cookie = demo_user_client
        client.headers["Cookie"] = cookie
        
        # Create skill
        skill_resp = await client.post(
            "/api/v1/skills",
            json={
                "name": "eval-list-skill",
                "display_name": "Eval List Skill",
                "description": "Skill for evaluation listing",
                "category": "evaluation",
                "schema": "{}",
            },
        )
        skill_id = skill_resp.json()["id"]
        
        # Create evaluation
        await client.post(
            f"/api/v1/skills/{skill_id}/evaluate",
            json={
                "skill_id": skill_id,
                "model_name": "gpt-4o",
                "model_version": "2024-08-06",
                "provider": "openai-compatible",
                "sample_size": 5,
            },
        )
        
        response = await client.get(f"/api/v1/skills/{skill_id}/evaluations")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    async def test_get_evaluation(self, demo_user_client):
        client, cookie = demo_user_client
        client.headers["Cookie"] = cookie
        
        # Create skill and evaluation
        skill_resp = await client.post(
            "/api/v1/skills",
            json={
                "name": "eval-get-skill",
                "display_name": "Eval Get Skill",
                "description": "Skill for evaluation get",
                "category": "evaluation",
                "schema": "{}",
            },
        )
        skill_id = skill_resp.json()["id"]
        
        eval_resp = await client.post(
            f"/api/v1/skills/{skill_id}/evaluate",
            json={
                "skill_id": skill_id,
                "model_name": "gpt-4o",
                "model_version": "2024-08-06",
                "provider": "openai-compatible",
                "sample_size": 5,
            },
        )
        eval_id = eval_resp.json()["id"]
        
        response = await client.get(f"/api/v1/skills/evaluations/{eval_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == eval_id


class TestDriftReports:
    async def test_create_drift_report(self, demo_user_client):
        client, cookie = demo_user_client
        client.headers["Cookie"] = cookie
        
        # Create skill
        skill_resp = await client.post(
            "/api/v1/skills",
            json={
                "name": "drift-test-skill",
                "display_name": "Drift Test Skill",
                "description": "Skill for drift testing",
                "category": "evaluation",
                "schema": "{}",
            },
        )
        skill_id = skill_resp.json()["id"]
        
        response = await client.post(
            "/api/v1/drift/reports",
            json={
                "skill_id": skill_id,
                "baseline_model": "gpt-4o",
                "baseline_version": "2024-05-13",
                "compare_model": "gpt-4o",
                "compare_version": "2024-08-06",
                "regression_detected": False,
                "effect_size": 0.02,
                "p_value": 0.45,
                "confidence_level": 0.95,
                "details": {"metric": "accuracy", "baseline": 0.85, "compare": 0.87},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["skill_id"] == skill_id
        assert data["regression_detected"] is False

    async def test_list_drift_reports(self, demo_user_client):
        client, cookie = demo_user_client
        client.headers["Cookie"] = cookie
        
        response = await client.get("/api/v1/drift/reports")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestAuditLogs:
    async def test_list_audit_logs(self, demo_user_client):
        client, cookie = demo_user_client
        client.headers["Cookie"] = cookie
        
        response = await client.get("/api/v1/drift/audit-logs")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data