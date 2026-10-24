"""
玉米病害字典模型。
"""
from __future__ import annotations

from sqlalchemy import Column, BigInteger, String, Text, DateTime, Index, Integer
from sqlalchemy.sql import func

from ..database import Base

IDType = BigInteger().with_variant(Integer, "sqlite")


class Disease(Base):
    __tablename__ = "diseases"
    __table_args__ = (
        Index("idx_name", "name"),
        Index("idx_crop", "crop_type"),
        {"comment": "玉米病害字典"},
    )

    id = Column(IDType, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, comment="病害名称")
    alias = Column(String(256), comment="别名（逗号分隔）")
    crop_type = Column(String(64), default="玉米", comment="作物类型")
    description = Column(Text, comment="病害描述")
    symptoms = Column(Text, comment="症状表现")
    causes = Column(Text, comment="发病原因")
    prevention = Column(Text, comment="防治方法")
    severity = Column(String(32), comment="危害程度：轻度/中度/重度")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
