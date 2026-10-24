"""
RAG 对话会话与消息模型。
"""
from __future__ import annotations

from sqlalchemy import Column, BigInteger, String, Text, Float, DateTime, Index, Boolean, JSON, Integer
from sqlalchemy.sql import func

from ..database import Base

IDType = BigInteger().with_variant(Integer, "sqlite")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = ({"comment": "RAG 对话会话"},)

    id = Column(IDType, primary_key=True, autoincrement=True)
    session_id = Column(String(128), unique=True, nullable=False, comment="会话唯一标识 UUID")
    title = Column(String(256), comment="会话标题")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("idx_session", "session_id"),
        Index("idx_created", "created_at"),
        {"comment": "RAG 对话消息"},
    )

    id = Column(IDType, primary_key=True, autoincrement=True)
    session_id = Column(String(128), nullable=False, comment="关联会话 session_id")
    role = Column(String(16), nullable=False, comment="user / assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    citations = Column(JSON, comment="引用来源 [{doc_id, doc_name, chunk_text, score}]")
    retrieval_score = Column(Float, comment="检索平均置信度")
    has_evidence = Column(Boolean, default=True, comment="是否有检索证据支撑")
    model_used = Column(String(128), comment="使用的模型")
    created_at = Column(DateTime, server_default=func.now())
