from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from ..services.recognition_service import RecognitionService

router = APIRouter(prefix="/api/recognition", tags=["病害识别"])


@router.post("/identify")
async def identify_disease(file: UploadFile = File(...)):
    """上传玉米叶片/植株图片，识别病害"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "只支持图片文件 (jpg/png/webp)")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(400, "图片不能超过 10MB")

    result = RecognitionService.identify(image_bytes, file.filename)
    return JSONResponse(result)
