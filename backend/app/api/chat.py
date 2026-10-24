from __future__ import annotations

import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..schemas import ChatRequest
from ..services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["RAG 问答"])


@router.post("/ask")
async def ask_chat(req: ChatRequest):
    """RAG 问答接口"""
    if not req.question or not req.question.strip():
        raise HTTPException(400, "问题不能为空")

    session_id = req.session_id or uuid.uuid4().hex[:12]

    history = [{"role": m.role, "content": m.content} for m in (req.history or [])]

    result = ChatService.answer(req.question, session_id=session_id, history=history, force_fixed_answer=req.force_fixed_answer or False)
    result["session_id"] = session_id
    return JSONResponse(result)
