"""
病害识别记录模型。
"""
from __future__ import annotations

from sqlalchemy import Column, BigInteger, String, Text, Float, Integer, DateTime, ForeignKey, Index, Boolean, JSON
from sqlalchemy.sql import func

from ..database import Base

IDType = BigInteger().with_variant(Integer, "sqlite")


class RecognitionRecord(Base):
    __tablename__ = "recognition_records"
    __table_args__ = (
        Index("idx_created", "created_at"),
        Index("idx_disease", "disease_id"),
        {"comment": "病害识别记录"},
    )

    id = Column(IDType, primary_key=True, autoincrement=True)
    image_path = Column(String(512), nullable=False, comment="图片存储路径")
    disease_id = Column(BigInteger, ForeignKey("diseases.id"), comment="关联病害 ID")
    confidence = Column(Float, comment="识别置信度 0-1")
    lesion_description = Column(Text, comment="病灶区域描述")
    model_used = Column(String(128), comment="使用的模型名称")
    demo_mode = Column(Boolean, default=False, comment="是否演示模式")
    top_candidates = Column(JSON, comment="候选病害列表 [{name, confidence}]")
    created_at = Column(DateTime, server_default=func.now())
