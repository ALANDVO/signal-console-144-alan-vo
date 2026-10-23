from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, String, Text, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0.0")
    schema: Mapped[str] = mapped_column(Text, nullable=False)  # JSON schema
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    evaluations: Mapped[list["Evaluation"]] = relationship(back_populates="skill", cascade="all, delete-orphan")
    drift_reports: Mapped[list["DriftReport"]] = relationship(back_populates="skill", cascade="all, delete-orphan")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")  # pending, running, completed, failed
    score: Mapped[Optional[float]] = mapped_column(nullable=True)
    confidence_lower: Mapped[Optional[float]] = mapped_column(nullable=True)
    confidence_upper: Mapped[Optional[float]] = mapped_column(nullable=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed: Mapped[Optional[bool]] = mapped_column(nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    eval_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    skill: Mapped["Skill"] = relationship(back_populates="evaluations")
    __table_args__ = (Index("ix_evaluations_skill_model", "skill_id", "model_name", "model_version"),)


class DriftReport(Base):
    __tablename__ = "drift_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    baseline_model: Mapped[str] = mapped_column(String(255), nullable=False)
    baseline_version: Mapped[str] = mapped_column(String(100), nullable=False)
    compare_model: Mapped[str] = mapped_column(String(255), nullable=False)
    compare_version: Mapped[str] = mapped_column(String(100), nullable=False)
    regression_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    effect_size: Mapped[Optional[float]] = mapped_column(nullable=True)
    p_value: Mapped[Optional[float]] = mapped_column(nullable=True)
    confidence_level: Mapped[float] = mapped_column(default=0.95, nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    skill: Mapped["Skill"] = relationship(back_populates="drift_reports")
    __table_args__ = (Index("ix_drift_reports_skill_models", "skill_id", "baseline_model", "compare_model"),)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    __table_args__ = (Index("ix_audit_logs_user_action", "user_id", "action"),)