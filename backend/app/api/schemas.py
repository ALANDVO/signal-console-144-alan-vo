from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)
    version: str = Field(default="1.0.0", max_length=50)
    schema: str = Field(..., min_length=1)  # JSON schema
    is_active: bool = True


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    version: Optional[str] = Field(None, max_length=50)
    schema: Optional[str] = Field(None, min_length=1)
    is_active: Optional[bool] = None


class SkillResponse(SkillBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class EvaluationBase(BaseModel):
    skill_id: int
    model_name: str = Field(..., min_length=1, max_length=255)
    model_version: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., min_length=1, max_length=100)
    sample_size: int = Field(default=5, ge=1, le=100)


class EvaluationCreate(EvaluationBase):
    pass


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    skill_id: int
    model_name: str
    model_version: str
    provider: str
    status: str
    score: Optional[float] = None
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
    sample_size: int
    passed: Optional[bool] = None
    error_message: Optional[str] = None
    metadata: Optional[str] = Field(None, validation_alias="eval_metadata")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


class DriftReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    skill_id: int
    baseline_model: str
    baseline_version: str
    compare_model: str
    compare_version: str
    regression_detected: bool
    effect_size: Optional[float] = None
    p_value: Optional[float] = None
    confidence_level: float
    details: str
    created_at: datetime


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int