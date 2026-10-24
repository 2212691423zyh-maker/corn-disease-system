"""
知识库文档、分块和版本模型。
"""
from __future__ import annotations

from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime, ForeignKey, Index, JSON
from sqlalchemy.sql import func

from ..database import Base

IDType = BigInteger().with_variant(Integer, "sqlite")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        Index("idx_status", "status"),
        Index("idx_filename", "filename"),
        {"comment": "知识库文档"},
    )

    id = Column(IDType, primary_key=True, autoincrement=True)
    filename = Column(String(256), nullable=False, comment="原始文件名")
    file_path = Column(String(512), nullable=False, comment="存储路径")
    doc_type = Column(String(32), nullable=False, comment="文档类型：pdf/word/txt")
    chunk_count = Column(Integer, default=0, comment="分块数量")
    file_size = Column(BigInteger, comment="文件大小（字节）")
    status = Column(String(32), default="uploaded", comment="uploaded/processing/indexed/failed")
    version = Column(String(32), default="v1.0", comment="版本号")
    error_msg = Column(Text, comment="失败时的错误信息")
    extra_meta = Column("metadata", JSON, comment="附加元数据")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        Index("idx_doc", "document_id"),
        Index("idx_chunk_id", "chunk_id"),
        {"comment": "知识库文档分块"},
    )

    id = Column(IDType, primary_key=True, autoincrement=True)
    document_id = Column(BigInteger, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False, comment="分块序号")
    chunk_id = Column(String(128), comment="FAISS 向量库中的 chunk 标识")
    content = Column(Text, nullable=False, comment="分块文本内容")
    token_count = Column(Integer, comment="Token 数量")
    created_at = Column(DateTime, server_default=func.now())


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = ({"comment": "文档版本历史"},)

    id = Column(IDType, primary_key=True, autoincrement=True)
    document_id = Column(BigInteger, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(32), nullable=False)
    file_path = Column(String(512), nullable=False)
    change_log = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
