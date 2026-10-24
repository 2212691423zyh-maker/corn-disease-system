from __future__ import annotations

import logging

from ..ai.qwen_vl import QwenVLClient
from ..ai.local_resnet import LocalResNetEngine
from ..rag.retriever import HybridRetriever

logger = logging.getLogger(__name__)


class RecognitionService:
    """病害识别服务：本地 ResNet50 优先 → Qwen-VL 兜底 → Mock 最终兜底 + RAG 知识支撑"""

    @classmethod
    def identify(cls, image_bytes: bytes, filename: str = "unknown.jpg") -> dict:
        # ---- 1. 图像识别：优先本地训练的 ResNet50，失败降级 Qwen-VL ----
        engine_name = "Local_ResNet50"
        try:
            local_engine = LocalResNetEngine()
            vl_result = local_engine.identify(image_bytes)
            logger.info("识别使用本地 ResNet50 模型")
        except Exception as e:
            logger.warning("本地 ResNet50 不可用，降级到 Qwen-VL: %s", e)
            vl = QwenVLClient()
            vl_result = vl.identify(image_bytes)
            engine_name = "Qwen-VL"

        disease_name = vl_result.get("name", "")
        confidence = vl_result.get("confidence", 0.5)
        symptoms = vl_result.get("symptoms", "")
        causes = vl_result.get("causes", "")
        top_candidates = vl_result.get("top_candidates", [])

        # ---- 2. RAG 补充知识 ----
        retriever = HybridRetriever.get()
        rag_chunks = []
        if disease_name:
            rag_chunks = retriever.search(
                f"{disease_name} 防治方法 原因 症状",
                top_k=5,
            )

        # ---- 3. 构造候选列表 ----
        candidates = top_candidates or [
            {
                "name": disease_name or "疑似玉米病害",
                "confidence": confidence,
                "symptoms": symptoms,
                "causes": causes,
            }
        ]

        # ---- 4. 返回结果 ----
        return {
            "primary": candidates[0],
            "top_candidates": candidates,
            "model_used": engine_name,
            "engine": engine_name,
            "rag_evidence": [
                {
                    "source": c.get("source", ""),
                    "text": c["text"][:300],
                    "score": round(c.get("score", 0), 3),
                }
                for c in rag_chunks
            ],
            "symptoms": symptoms,
            "confidence": confidence,
            "lesion_description": symptoms,
        }
