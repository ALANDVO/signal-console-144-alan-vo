from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db_session
from app.core.auth import require_user, require_role, log_audit
from app.services import (
    get_skill,
    create_drift_report,
    list_drift_reports,
    list_audit_logs,
)
from app.api.schemas import (
    DriftReportResponse,
    AuditLogResponse,
    PaginatedResponse,
)
from app.core.exceptions import NotFoundError
from fastapi import Request


router = APIRouter(prefix="/drift", tags=["drift"])


@router.get("/reports", response_model=PaginatedResponse)
async def list_drift_reports_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    skill_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_user),
) -> PaginatedResponse:
    if skill_id:
        await get_skill(db, skill_id)
    reports, total = await list_drift_reports(db, page=page, page_size=page_size, skill_id=skill_id)
    return PaginatedResponse(
        items=[DriftReportResponse.model_validate(r) for r in reports],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("/reports", response_model=DriftReportResponse, status_code=status.HTTP_201_CREATED)
async def create_drift_report_endpoint(
    request_data: dict,
    db: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(require_role(["admin", "operator"])),
    request: Request = None,
) -> DriftReportResponse:
    skill_id = request_data.get("skill_id")
    baseline_model = request_data.get("baseline_model")
    baseline_version = request_data.get("baseline_version")
    compare_model = request_data.get("compare_model")
    compare_version = request_data.get("compare_version")
    regression_detected = request_data.get("regression_detected", False)
    effect_size = request_data.get("effect_size")
    p_value = request_data.get("p_value")
    confidence_level = request_data.get("confidence_level", 0.95)
    details = request_data.get("details", {})
    
    await get_skill(db, skill_id)
    report = await create_drift_report(
        db,
        skill_id=skill_id,
        baseline_model=baseline_model,
        baseline_version=baseline_version,
        compare_model=compare_model,
        compare_version=compare_version,
        regression_detected=regression_detected,
        effect_size=effect_size,
        p_value=p_value,
        confidence_level=confidence_level,
        details=details,
    )
    await log_audit(db, user_id, "create", "drift_report", str(report.id), {"skill_id": skill_id}, request)
    return DriftReportResponse.model_validate(report)


@router.get("/audit-logs", response_model=PaginatedResponse)
async def list_audit_logs_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    user_id_dep: str = Depends(require_role(["admin", "operator"])),
) -> PaginatedResponse:
    logs, total = await list_audit_logs(db, page=page, page_size=page_size, user_id=user_id, action=action)
    return PaginatedResponse(
        items=[AuditLogResponse.model_validate(l) for l in logs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )