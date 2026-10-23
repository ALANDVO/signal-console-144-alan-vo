from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Skill, Evaluation, DriftReport, AuditLog
from app.api.schemas import SkillCreate, SkillUpdate, EvaluationCreate
from app.core.exceptions import NotFoundError, ConflictError


async def create_skill(session: AsyncSession, skill_data: SkillCreate) -> Skill:
    existing = await session.execute(select(Skill).where(Skill.name == skill_data.name))
    if existing.scalar_one_or_none():
        raise ConflictError(f"Skill with name '{skill_data.name}' already exists")

    skill = Skill(**skill_data.model_dump())
    session.add(skill)
    await session.flush()
    await session.refresh(skill)
    return skill


async def get_skill(session: AsyncSession, skill_id: int) -> Skill:
    result = await session.execute(
        select(Skill).where(Skill.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise NotFoundError("Skill", str(skill_id))
    return skill


async def get_skill_by_name(session: AsyncSession, name: str) -> Skill:
    result = await session.execute(select(Skill).where(Skill.name == name))
    skill = result.scalar_one_or_none()
    if not skill:
        raise NotFoundError("Skill", name)
    return skill


async def list_skills(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
) -> tuple[List[Skill], int]:
    query = select(Skill)
    
    if category:
        query = query.where(Skill.category == category)
    if is_active is not None:
        query = query.where(Skill.is_active == is_active)
    if search:
        query = query.where(
            Skill.name.ilike(f"%{search}%") | Skill.display_name.ilike(f"%{search}%")
        )
    
    total_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(total_query)
    
    query = query.order_by(Skill.name).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    skills = result.scalars().all()
    
    return list(skills), total


async def update_skill(session: AsyncSession, skill_id: int, skill_data: SkillUpdate) -> Skill:
    skill = await get_skill(session, skill_id)
    
    update_data = skill_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(skill, field, value)
    
    await session.flush()
    await session.refresh(skill)
    return skill


async def delete_skill(session: AsyncSession, skill_id: int) -> None:
    skill = await get_skill(session, skill_id)
    await session.delete(skill)
    await session.flush()


async def create_evaluation(session: AsyncSession, eval_data: EvaluationCreate) -> Evaluation:
    skill = await get_skill(session, eval_data.skill_id)
    
    evaluation = Evaluation(
        skill_id=eval_data.skill_id,
        model_name=eval_data.model_name,
        model_version=eval_data.model_version,
        provider=eval_data.provider,
        sample_size=eval_data.sample_size,
        status="pending",
    )
    session.add(evaluation)
    await session.flush()
    await session.refresh(evaluation)
    return evaluation


async def get_evaluation(session: AsyncSession, eval_id: int) -> Evaluation:
    result = await session.execute(
        select(Evaluation).where(Evaluation.id == eval_id)
    )
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise NotFoundError("Evaluation", str(eval_id))
    return evaluation


async def list_evaluations(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    skill_id: Optional[int] = None,
    status: Optional[str] = None,
) -> tuple[List[Evaluation], int]:
    query = select(Evaluation).options(selectinload(Evaluation.skill))
    
    if skill_id:
        query = query.where(Evaluation.skill_id == skill_id)
    if status:
        query = query.where(Evaluation.status == status)
    
    total_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(total_query)
    
    query = query.order_by(desc(Evaluation.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    evaluations = result.scalars().all()
    
    return list(evaluations), total


async def update_evaluation_status(
    session: AsyncSession,
    eval_id: int,
    status: str,
    score: Optional[float] = None,
    confidence_lower: Optional[float] = None,
    confidence_upper: Optional[float] = None,
    passed: Optional[bool] = None,
    error_message: Optional[str] = None,
    metadata: Optional[str] = None,
) -> Evaluation:
    evaluation = await get_evaluation(session, eval_id)
    
    evaluation.status = status
    if score is not None:
        evaluation.score = score
    if confidence_lower is not None:
        evaluation.confidence_lower = confidence_lower
    if confidence_upper is not None:
        evaluation.confidence_upper = confidence_upper
    if passed is not None:
        evaluation.passed = passed
    if error_message is not None:
        evaluation.error_message = error_message
    if metadata is not None:
        evaluation.metadata = metadata
    if status in ("completed", "failed"):
        evaluation.completed_at = datetime.now(timezone.utc)
    if status == "running":
        evaluation.started_at = datetime.now(timezone.utc)
    
    await session.flush()
    await session.refresh(evaluation)
    return evaluation


async def create_drift_report(
    session: AsyncSession,
    skill_id: int,
    baseline_model: str,
    baseline_version: str,
    compare_model: str,
    compare_version: str,
    regression_detected: bool,
    effect_size: Optional[float],
    p_value: Optional[float],
    confidence_level: float,
    details: Dict[str, Any],
) -> DriftReport:
    import json
    skill = await get_skill(session, skill_id)
    
    report = DriftReport(
        skill_id=skill_id,
        baseline_model=baseline_model,
        baseline_version=baseline_version,
        compare_model=compare_model,
        compare_version=compare_version,
        regression_detected=regression_detected,
        effect_size=effect_size,
        p_value=p_value,
        confidence_level=confidence_level,
        details=json.dumps(details),
    )
    session.add(report)
    await session.flush()
    await session.refresh(report)
    return report


async def list_drift_reports(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    skill_id: Optional[int] = None,
) -> tuple[List[DriftReport], int]:
    query = select(DriftReport).options(selectinload(DriftReport.skill))
    
    if skill_id:
        query = query.where(DriftReport.skill_id == skill_id)
    
    total_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(total_query)
    
    query = query.order_by(desc(DriftReport.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    reports = result.scalars().all()
    
    return list(reports), total


async def list_audit_logs(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 50,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
) -> tuple[List[AuditLog], int]:
    query = select(AuditLog)
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
    
    total_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(total_query)
    
    query = query.order_by(desc(AuditLog.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    logs = result.scalars().all()
    
    return list(logs), total