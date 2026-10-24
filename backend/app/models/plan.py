"""
防治方案与导出记录模型。
"""
from __future__ import annotations

from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, Index, JSON, Integer
from sqlalchemy.sql import func

from ..database import Base

IDType = BigInteger().with_variant(Integer, "sqlite")


class PreventionPlan(Base):
    __tablename__ = "prevention_plans"
    __table_args__ = (
        Index("idx_recognition", "recognition_id"),
        Index("idx_disease_plan", "disease_id"),
        {"comment": "防治方案"},
    )

    id = Column(IDType, primary_key=True, autoincrement=True)
    recognition_id = Column(BigInteger, ForeignKey("recognition_records.id"))
    disease_id = Column(BigInteger, ForeignKey("diseases.id"))
    plan_title = Column(String(256), nullable=False, comment="方案标题")
    medication_plan = Column(JSON, comment="用药方案 [{drug, dosage, frequency, precautions}]")
    fertilization_plan = Column(JSON, comment="施肥方案 [{type, dosage, timing}]")
    prevention_tips = Column(Text, comment="综合防治建议")
    agricultural_operations = Column(Text, comment="农业操作建议")
    rag_evidence = Column(JSON, comment="RAG 支撑证据 [{doc_name, chunk_text, citation}]")
    status = Column(String(16), default="draft", comment="draft / final")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PlanExport(Base):
    __tablename__ = "plan_exports"
    __table_args__ = (
        Index("idx_plan", "plan_id"),
        {"comment": "方案导出记录"},
    )

    id = Column(IDType, primary_key=True, autoincrement=True)
    plan_id = Column(BigInteger, ForeignKey("prevention_plans.id", ondelete="CASCADE"), nullable=False)
    format = Column(String(16), nullable=False, comment="pdf / word")
    file_path = Column(String(512), nullable=False)
    file_size = Column(BigInteger)
    created_at = Column(DateTime, server_default=func.now())
