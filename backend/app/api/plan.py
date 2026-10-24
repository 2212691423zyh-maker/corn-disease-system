from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from ..schemas import PlanGenerateRequest
from ..services.plan_service import PlanService
from ..config import settings

router = APIRouter(prefix="/api/plan", tags=["防治方案"])


@router.post("/generate")
async def generate_plan(req: PlanGenerateRequest):
    """根据病害名称和症状生成防治方案"""
    if not req.disease_name:
        raise HTTPException(400, "病害名称不能为空")

    result = PlanService.generate(req.disease_name, req.symptoms)
    return JSONResponse(result)


@router.post("/export/{plan_id}")
async def export_plan_word(plan_id: int, body: dict):
    """将方案导出为 Word 文档"""
    try:
        plan = body or {}
        export_info = PlanService.export_word(plan, plan_id)
    except Exception as e:
        raise HTTPException(500, f"导出失败: {e}")

    file_path = export_info["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(404, "导出文件不存在")

    return FileResponse(
        path=file_path,
        filename=export_info["filename"],
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{export_info["filename"]}"'},
    )
