import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services import create_skill, list_skills, get_skill, update_skill, delete_skill
from app.api.schemas import SkillCreate, SkillUpdate
from app.core.exceptions import NotFoundError, ConflictError


class TestSkillService:
    async def test_create_skill(self, test_session: AsyncSession):
        skill_data = SkillCreate(
            name="service-test",
            display_name="Service Test",
            description="Test skill via service",
            category="evaluation",
            schema="{}",
        )
        skill = await create_skill(test_session, skill_data)
        assert skill.id is not None
        assert skill.name == "service-test"
        assert skill.display_name == "Service Test"

    async def test_create_duplicate_skill_raises_conflict(self, test_session: AsyncSession):
        skill_data = SkillCreate(
            name="duplicate-service",
            display_name="Duplicate Service",
            description="Test",
            category="evaluation",
            schema="{}",
        )
        await create_skill(test_session, skill_data)
        
        with pytest.raises(ConflictError):
            await create_skill(test_session, skill_data)

    async def test_get_skill(self, test_session: AsyncSession):
        skill_data = SkillCreate(
            name="get-service-test",
            display_name="Get Service Test",
            description="Test",
            category="evaluation",
            schema="{}",
        )
        created = await create_skill(test_session, skill_data)
        
        skill = await get_skill(test_session, created.id)
        assert skill.id == created.id
        assert skill.name == "get-service-test"

    async def test_get_nonexistent_skill_raises_not_found(self, test_session: AsyncSession):
        with pytest.raises(NotFoundError):
            await get_skill(test_session, 99999)

    async def test_list_skills(self, test_session: AsyncSession):
        for i in range(3):
            await create_skill(test_session, SkillCreate(
                name=f"list-test-{i}",
                display_name=f"List Test {i}",
                description="Test",
                category="evaluation",
                schema="{}",
            ))
        
        skills, total = await list_skills(test_session, page=1, page_size=10)
        assert total >= 3
        assert len(skills) >= 3

    async def test_list_skills_with_filter(self, test_session: AsyncSession):
        await create_skill(test_session, SkillCreate(
            name="filter-test-active",
            display_name="Filter Active",
            description="Test",
            category="evaluation",
            schema="{}",
            is_active=True,
        ))
        await create_skill(test_session, SkillCreate(
            name="filter-test-inactive",
            display_name="Filter Inactive",
            description="Test",
            category="evaluation",
            schema="{}",
            is_active=False,
        ))
        
        skills, total = await list_skills(test_session, page=1, page_size=10, is_active=True)
        assert total >= 1
        assert all(s.is_active for s in skills)

    async def test_update_skill(self, test_session: AsyncSession):
        skill_data = SkillCreate(
            name="update-service-test",
            display_name="Update Service Test",
            description="Test",
            category="evaluation",
            schema="{}",
        )
        created = await create_skill(test_session, skill_data)
        
        updated = await update_skill(test_session, created.id, SkillUpdate(
            display_name="Updated Display Name",
            description="Updated description",
        ))
        assert updated.display_name == "Updated Display Name"
        assert updated.description == "Updated description"
        assert updated.name == "update-service-test"  # Unchanged

    async def test_delete_skill(self, test_session: AsyncSession):
        skill_data = SkillCreate(
            name="delete-service-test",
            display_name="Delete Service Test",
            description="Test",
            category="evaluation",
            schema="{}",
        )
        created = await create_skill(test_session, skill_data)
        
        await delete_skill(test_session, created.id)
        
        with pytest.raises(NotFoundError):
            await get_skill(test_session, created.id)