from fastapi import APIRouter, Depends, Query, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db_session
from app.core.auth import require_user, require_role, log_audit
from app.services import (
    create_skill,
    get_skill,
    get_skill_by_name,
    list_skills,
    update_skill,
    delete_skill,
    create_evaluation,
    get_evaluation,
    list_evaluations,
    update_evaluation_status,
)
from app.api.schemas import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    EvaluationCreate,
    EvaluationResponse,
    PaginatedResponse,
)
from app.core.exceptions import NotFoundError, ForbiddenError


router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=PaginatedResponse)
async def list_skills_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_user),
) -> PaginatedResponse:
    skills, total = await list_skills(
        db, page=page, page_size=page_size, category=category, is_active=is_active, search=search
    )
    return PaginatedResponse(
        items=[SkillResponse.model_validate(s) for s in skills],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill_endpoint(
    skill_id: int,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_user),
) -> SkillResponse:
    skill = await get_skill(db, skill_id)
    return SkillResponse.model_validate(skill)


@router.get("/by-name/{name}", response_model=SkillResponse)
async def get_skill_by_name_endpoint(
    name: str,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_user),
) -> SkillResponse:
    skill = await get_skill_by_name(db, name)
    return SkillResponse.model_validate(skill)


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill_endpoint(
    skill_data: SkillCreate,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_role(["admin", "operator"])),
    request: Request = None,
) -> SkillResponse:
    skill = await create_skill(db, skill_data)
    await log_audit(db, user_id, "create", "skill", str(skill.id), {"name": skill.name}, request)
    return SkillResponse.model_validate(skill)


@router.patch("/{skill_id}", response_model=SkillResponse)
async def update_skill_endpoint(
    skill_id: int,
    skill_data: SkillUpdate,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_role(["admin", "operator"])),
    request: Request = None,
) -> SkillResponse:
    skill = await update_skill(db, skill_id, skill_data)
    await log_audit(db, user_id, "update", "skill", str(skill_id), skill_data.model_dump(exclude_unset=True), request)
    return SkillResponse.model_validate(skill)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill_endpoint(
    skill_id: int,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_role(["admin"])),
    request: Request = None,
) -> None:
    await delete_skill(db, skill_id)
    await log_audit(db, user_id, "delete", "skill", str(skill_id), {}, request)


@router.post("/{skill_id}/evaluate", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation_endpoint(
    skill_id: int,
    eval_data: EvaluationCreate,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_role(["admin", "operator", "analyst"])),
    request: Request = None,
) -> EvaluationResponse:
    if eval_data.skill_id != skill_id:
        raise HTTPException(status_code=400, detail="Skill ID mismatch")
    
    evaluation = await create_evaluation(db, eval_data)
    await log_audit(db, user_id, "create", "evaluation", str(evaluation.id), eval_data.model_dump(), request)
    return EvaluationResponse.model_validate(evaluation)


@router.get("/{skill_id}/evaluations", response_model=PaginatedResponse)
async def list_skill_evaluations(
    skill_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_user),
) -> PaginatedResponse:
    await get_skill(db, skill_id)  # Validate skill exists
    evaluations, total = await list_evaluations(db, page=page, page_size=page_size, skill_id=skill_id, status=status)
    return PaginatedResponse(
        items=[EvaluationResponse.model_validate(e) for e in evaluations],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/evaluations/{eval_id}", response_model=EvaluationResponse)
async def get_evaluation_endpoint(
    eval_id: int,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_user),
) -> EvaluationResponse:
    evaluation = await get_evaluation(db, eval_id)
    return EvaluationResponse.model_validate(evaluation)