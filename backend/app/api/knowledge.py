from __future__ import annotations

import os
import itertools
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..services.knowledge_service import KnowledgeService
from ..rag.retriever import HybridRetriever

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])

_id_counter = itertools.count(1)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传 PDF/Word/TXT 文档到知识库"""
    allowed = {"pdf", "doc", "docx", "txt"}
    ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if ext not in allowed:
        raise HTTPException(400, f"只支持 {', '.join(allowed)} 文件")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(400, "文件不能超过 50MB")

    document_id = next(_id_counter)
    result = KnowledgeService.index_document(file.filename, content, document_id=document_id)

    return JSONResponse({
        "status": result.get("status", "indexed"),
        "filename": file.filename,
        "doc_type": result.get("doc_type", ext),
        "chunk_count": result.get("chunk_count", 0),
        "error": result.get("error"),
    })


@router.get("/stats")
async def knowledge_stats():
    """返回知识库统计"""
    retriever = HybridRetriever.get()
    return JSONResponse({
        "indexed_chunks": len(retriever.chunks_meta),
        "index_present": retriever.index is not None,
        "bm25_present": retriever.bm25 is not None,
    })


@router.get("/documents")
async def list_documents():
    """获取知识库文档列表"""
    docs = KnowledgeService.list_documents()
    return JSONResponse({"documents": docs, "total": len(docs)})


@router.delete("/documents/{document_id}")
async def delete_document(document_id: int):
    """删除知识库文档"""
    ok = KnowledgeService.delete_document(document_id)
    if not ok:
        raise HTTPException(404, f"文档 {document_id} 不存在")
    return JSONResponse({"status": "deleted", "document_id": document_id})
