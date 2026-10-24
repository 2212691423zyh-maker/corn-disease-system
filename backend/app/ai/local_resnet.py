from __future__ import annotations

import os
import sys
import tempfile
from typing import Optional

from ..config import settings


# ============================================================
# 本地训练的 ResNet50 模型引擎
# 优先于 Qwen-VL / Mock 使用，便于答辩时展示本地模型效果
# ============================================================

# 训练目录（含 predict.py 和 outputs/）
TRAIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "train"))
# 微调模型权重绝对路径
WEIGHTS_PATH = os.path.join(TRAIN_DIR, "outputs", "finetune", "best_model.pt")

# 只在首次调用时 import predict，避免后端启动时强依赖 torch
_predict_module = None


def _ensure_predict_loaded():
    """动态加载 train/predict.py（含其依赖 data_loader），失败时抛异常由上层降级"""
    global _predict_module
    if _predict_module is not None:
        return _predict_module

    if not os.path.isdir(TRAIN_DIR):
        raise RuntimeError(f"训练目录不存在: {TRAIN_DIR}")
    if TRAIN_DIR not in sys.path:
        sys.path.insert(0, TRAIN_DIR)

    import predict  # noqa: WPS433
    _predict_module = predict
    return predict


class LocalResNetEngine:
    """本地训练的 ResNet50 玉米病害识别引擎

    答辩优先展示引擎。识别结果带 engine="Local_ResNet50" 标识。
    模型文件丢失或推理异常时抛异常，由上层降级到 Qwen-VL / Mock。
    """

    ENGINE_NAME = "Local_ResNet50"

    # 4 类病害的症状与病因描述（用于补充返回，与前端展示字段对齐）
    _DISEASE_INFO = {
        "灰斑病": {
            "symptoms": "叶片出现灰褐色椭圆形或长条形病斑，中央灰白色，边缘褐色",
            "causes": "玉蜀黍尾孢菌侵染，高温高湿（25-30℃，相对湿度>90%）条件下易暴发",
        },
        "普通锈病": {
            "symptoms": "叶片正反两面出现红褐色粉状夏孢子堆，破裂后散出铁锈色粉末",
            "causes": "高粱柄锈菌侵染，冷凉潮湿气候（16-23℃）下发生较重",
        },
        "北方叶枯病": {
            "symptoms": "叶片出现大型梭形灰褐色病斑，湿度大时病斑上产生黑色霉层",
            "causes": "大斑刚毛球腔菌侵染，温度偏低（18-22℃）、多雨寡照时流行",
        },
        "健康叶片": {
            "symptoms": "叶片颜色正常，无明显病斑、霉层或坏死区域",
            "causes": "未检测到明显病害特征，建议结合田间观察定期复查",
        },
    }

    @classmethod
    def is_available(cls) -> bool:
        """检查模型权重是否存在，用于启动时自检"""
        return os.path.exists(WEIGHTS_PATH)

    def identify(self, image_bytes: bytes) -> dict:
        """识别图片中的玉米病害，返回标准化 JSON

        返回字段与 QwenVLClient.identify 兼容，并额外带 engine 标识。
        """
        predict = _ensure_predict_loaded()

        # 写临时文件供 predict.predict 使用
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                f.write(image_bytes)
                tmp_path = f.name

            result = predict.predict(tmp_path, weights_path=WEIGHTS_PATH)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

        disease_name = result["class_name"]
        confidence = result["probability"]
        info = self._DISEASE_INFO.get(disease_name, {})

        return {
            "name": disease_name,
            "confidence": confidence,
            "symptoms": info.get("symptoms", ""),
            "causes": info.get("causes", ""),
            "engine": self.ENGINE_NAME,
            "top_candidates": [
                {
                    "name": c["class_name"],
                    "confidence": c["probability"],
                }
                for c in result.get("top_k", [])
            ],
        }
