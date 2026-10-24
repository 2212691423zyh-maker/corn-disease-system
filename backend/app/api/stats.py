from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..ai.embedding import BGEEmbedder
from ..rag.retriever import HybridRetriever
from ..config import settings

router = APIRouter(prefix="/api/stats", tags=["统计看板"])


@router.get("/overview")
async def stats_overview():
    """看板概览数据（Mock 实现，数据库连通时可替换为真实查询）"""
    retriever = HybridRetriever.get()

    return JSONResponse({
        "total_documents": len(set(c.get("document_id", 0) for c in retriever.chunks_meta)) if retriever.chunks_meta else 0,
        "total_chunks": len(retriever.chunks_meta),
        "retrieval_ready": retriever.index is not None and len(retriever.chunks_meta) > 0,
        "engine_config": {
            "bge_model": settings.BGE_MODEL_PATH,
            "reranker_model": settings.RERANKER_MODEL_PATH,
            "device": settings.DEVICE,
            "force_demo": settings.FORCE_DEMO_MODE,
            "fixed_answer": settings.DEMO_FIXED_ANSWER,
        },
        "note": "数据库表结构已就绪，插入预置数据后重启即可获得真实统计",
    })
