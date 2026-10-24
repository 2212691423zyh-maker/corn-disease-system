from __future__ import annotations

import base64
import hashlib
import time
from typing import Optional

import httpx

from ..config import settings


class QwenVLClient:
    """Qwen-VL 图像识别客户端（阿里云 DashScope 云端 API）"""

    VISION_MODEL = "qwen-vl-plus"

    def __init__(self):
        self.api_key = settings.QWEN_API_KEY
        self.url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        self.mock = not self.api_key or settings.FORCE_DEMO_MODE

    def identify(self, image_bytes: bytes, prompt: str = "这是一张玉米叶片或植株的照片，请识别可能的病虫害。返回 JSON 格式: {\"name\": \"病害名\", \"confidence\": 0-1, \"symptoms\": \"描述\", \"causes\": \"原因\"}") -> dict:
        """识别图片中的病害，返回标准化 JSON"""
        if self.mock:
            return self._mock_result(image_bytes)

        img_b64 = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "model": self.VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        }

        try:
            resp = httpx.post(
                self.url,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            import json, re
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                match = re.search(r"\{.*\}", content, re.DOTALL)
                return json.loads(match.group()) if match else self._mock_result(image_bytes)
        except Exception as e:
            print(f"[Qwen-VL] 调用失败，降级 Mock: {e}")
            return self._mock_result(image_bytes)

    def _mock_result(self, image_bytes: bytes) -> dict:
        """基于图片 hash 生成稳定但多样化的 Mock 结果"""
        h = int(hashlib.md5(image_bytes).hexdigest(), 16)
        diseases = [
            ("玉米南方锈病", 0.92, "叶片出现橙黄色粉状孢子堆"),
            ("玉米大斑病", 0.88, "叶片出现大型梭形灰褐色病斑"),
            ("玉米小斑病", 0.85, "叶片上出现小型椭圆形黄褐色病斑"),
            ("玉米纹枯病", 0.82, "茎基部出现云纹状褐色病斑"),
            ("玉米丝黑穗病", 0.78, "果穗被破坏成黑粉包状"),
            ("玉米普通锈病", 0.80, "叶片背面有黄褐色粉状夏孢子堆"),
        ]
        name, conf, sym = diseases[h % len(diseases)]
        return {
            "name": name,
            "confidence": round(conf * (0.85 + (h % 100) / 667), 3),
            "symptoms": sym,
            "causes": "高温高湿条件下真菌侵染（Mock 演示数据）",
        }
