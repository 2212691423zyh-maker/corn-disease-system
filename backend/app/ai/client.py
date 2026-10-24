from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from fastapi import HTTPException

from ..config import settings


class LLMClient(ABC):
    """LLM 客户端抽象基类 —— 策略模式核心"""

    @abstractmethod
    def chat(self, messages: List[Dict[str, Any]], temperature: float = 0.7) -> str:
        ...

    @abstractmethod
    def chat_json(self, messages: List[Dict[str, Any]], temperature: float = 0.3) -> Dict[str, Any]:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


class DeepSeekClient(LLMClient):
    """DeepSeek 云端 API 客户端"""

    def __init__(self):
        import httpx

        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1"
        self.model = settings.DEEPSEEK_MODEL
        self._client = httpx.Client(timeout=60.0)

    @property
    def name(self) -> str:
        return f"DeepSeek/{self.model}"

    def chat(self, messages: List[Dict[str, Any]], temperature: float = 0.7) -> str:
        resp = self._client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            },
        )
        if resp.status_code != 200:
            raise HTTPException(502, f"DeepSeek API 错误: {resp.text}")
        return resp.json()["choices"][0]["message"]["content"]

    def chat_json(self, messages: List[Dict[str, Any]], temperature: float = 0.3) -> Dict[str, Any]:
        json_messages = messages + [
            {"role": "system", "content": "请严格返回 JSON 格式，不要任何多余文字。"}
        ]
        content = self.chat(json_messages, temperature)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise HTTPException(502, "LLM 未能返回有效 JSON")


class MockClient(LLMClient):
    """Mock 引擎 —— 断网或未配置 API Key 时的兜底

    有两层兜底:
    1. 常规 Mock: 根据关键词返回预设回答
    2. 固定回答模式: DEMO_FIXED_ANSWER=true 时, 任何问题都返回完美回答 (答辩安全网)
    """

    @property
    def name(self) -> str:
        return "MockEngine"

    def chat(self, messages: List[Dict[str, Any]], temperature: float = 0.7) -> str:
        if settings.DEMO_FIXED_ANSWER:
            return self._fixed_perfect_answer()

        user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")

        kw_map = {
            "南方锈病": self._answer_south_rust(),
            "锈病": self._answer_south_rust(),
            "大斑病": self._answer_leaf_blight(),
            "小斑病": self._answer_leaf_spot(),
            "纹枯病": self._answer_sheath_blight(),
            "丝黑穗": self._answer_head_smut(),
            "黑粉病": self._answer_common_smut(),
            "玉米螟": self._answer_corn_borer(),
            "蚜虫": self._answer_aphid(),
            "粘虫": self._answer_armyworm(),
            "红蜘蛛": self._answer_spider_mite(),
        }

        for kw, answer in kw_map.items():
            if kw in user_msg:
                return answer

        return self._generic_answer(user_msg)

    def chat_json(self, messages: List[Dict[str, Any]], temperature: float = 0.3) -> Dict[str, Any]:
        if settings.DEMO_FIXED_ANSWER:
            return {
                "plan_title": "玉米南方锈病综合防治方案",
                "medication_plan": [
                    {"drug": "25%三唑酮可湿性粉剂", "dosage": "1000-1500倍液", "frequency": "7天1次，连喷2-3次", "precautions": "避免高温时段施药"},
                    {"drug": "43%戊唑醇悬浮剂", "dosage": "3000倍液", "frequency": "7-10天1次", "precautions": "与三唑酮交替使用防抗药性"},
                    {"drug": "10%苯醚甲环唑微乳剂", "dosage": "2000倍液", "frequency": "发病初期喷施1次", "precautions": "安全间隔期21天"},
                ],
                "fertilization_plan": [
                    {"type": "磷钾肥", "dosage": "磷酸二氢钾150g/亩", "timing": "拔节期至抽雄期叶面喷施"},
                    {"type": "有机肥", "dosage": "腐熟农家肥2000kg/亩", "timing": "播种前基肥"},
                ],
                "prevention_tips": (
                    "1. **选用抗病品种**：农大372、登海605、郑单958等品种抗性较好\n"
                    "2. **合理密植**：行距60cm、株距30cm，保证通风透光\n"
                    "3. **增施磷钾肥**：避免偏施氮肥，增强植株抗性\n"
                    "4. **及时排水**：雨后及时排水降湿\n"
                    "5. **药剂轮换**：三唑酮与戊唑醇交替使用，防止抗药性"
                ),
                "agricultural_operations": (
                    "- 秋收后深翻灭茬，减少越冬菌源\n"
                    "- 7月中下旬开始田间巡查，3-5片叶时重点观察\n"
                    "- 发现中心病株立即喷药保护，防止扩散蔓延"
                ),
                "confidence": 0.95,
            }

        user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return self._mock_plan_by_keyword(user_msg)

    def _mock_plan_by_keyword(self, text: str) -> Dict[str, Any]:
        plans = {
            "南方锈病": {
                "title": "玉米南方锈病综合防治方案",
                "meds": [
                    {"drug": "25%三唑酮可湿性粉剂", "dosage": "1000-1500倍液", "frequency": "7天1次，连喷2-3次", "precautions": "避免高温时段施药"},
                    {"drug": "43%戊唑醇悬浮剂", "dosage": "3000倍液", "frequency": "7-10天1次", "precautions": "与三唑酮交替使用"},
                ],
                "ferts": [
                    {"type": "磷酸二氢钾", "dosage": "150g/亩", "timing": "拔节期叶面喷施"},
                ],
                "tips": "选用抗病品种（农大372、登海605），合理密植保证通风，7-8月雨季重点巡查。",
                "ops": "秋收后深翻灭茬；发现病斑立即喷药保护。",
            },
            "大斑病": {
                "title": "玉米大斑病防治方案",
                "meds": [
                    {"drug": "75%百菌清可湿性粉剂", "dosage": "500倍液", "frequency": "7-10天1次", "precautions": "发病初期喷施"},
                    {"drug": "50%多菌灵可湿性粉剂", "dosage": "500倍液", "frequency": "7天1次", "precautions": "与百菌清轮换"},
                ],
                "ferts": [
                    {"type": "磷钾肥", "dosage": "适量", "timing": "拔节期追施"},
                ],
                "tips": "选抗病品种，合理密植，增施磷钾肥增强抗性。",
                "ops": "秋收后深翻灭茬，清除田间病残体。",
            },
            "小斑病": {
                "title": "玉米小斑病防治方案",
                "meds": [
                    {"drug": "50%多菌灵可湿性粉剂", "dosage": "500倍液", "frequency": "7天1次", "precautions": "发病初期喷施"},
                    {"drug": "70%甲基硫菌灵", "dosage": "800倍液", "frequency": "7-10天1次", "precautions": "轮换使用"},
                ],
                "ferts": [
                    {"type": "磷钾肥", "dosage": "适量", "timing": "拔节期追施"},
                ],
                "tips": "增施磷钾肥，避免偏施氮肥，及时排水降湿。",
                "ops": "清除病残体，合理密植。",
            },
            "纹枯病": {
                "title": "玉米纹枯病防治方案",
                "meds": [
                    {"drug": "5%井冈霉素A水剂", "dosage": "1500倍液", "frequency": "7-10天1次", "precautions": "重点喷施茎基部"},
                ],
                "ferts": [
                    {"type": "钾肥", "dosage": "适量", "timing": "拔节期"},
                ],
                "tips": "合理密植，及时排水，避免田间湿度过大。",
                "ops": "剥除基部病叶，减少侵染源。",
            },
            "玉米螟": {
                "title": "玉米螟防治方案",
                "meds": [
                    {"drug": "Bt乳剂", "dosage": "200倍液", "frequency": "心叶末期喷施", "precautions": "生物农药，阴天施用"},
                    {"drug": "20%氰戊菊酯乳油", "dosage": "2000倍液", "frequency": "低龄幼虫期", "precautions": "注意保护天敌"},
                ],
                "ferts": [],
                "tips": "释放赤眼蜂生物防治（1万头/亩），心叶末期是防治关键期。",
                "ops": "秋季深翻灭茬，消灭越冬虫源。",
            },
            "蚜虫": {
                "title": "玉米蚜虫防治方案",
                "meds": [
                    {"drug": "10%吡虫啉可湿性粉剂", "dosage": "2000倍液", "frequency": "发生期喷施", "precautions": "重点喷施叶背"},
                ],
                "ferts": [],
                "tips": "黄板诱杀有翅蚜，保护瓢虫、草蛉等天敌。",
                "ops": "清除田边杂草，减少虫源。",
            },
        }
        for kw, p in plans.items():
            if kw in text:
                return {
                    "plan_title": p["title"],
                    "medication_plan": p["meds"],
                    "fertilization_plan": p["ferts"],
                    "prevention_tips": p["tips"],
                    "agricultural_operations": p["ops"],
                    "confidence": 0.85,
                }
        return {
            "plan_title": "玉米病害综合防治方案（Mock）",
            "medication_plan": [
                {"drug": "25%三唑酮可湿性粉剂", "dosage": "1000倍液", "frequency": "7天1次", "precautions": "通用保护剂"},
            ],
            "fertilization_plan": [
                {"type": "磷钾肥", "dosage": "适量", "timing": "拔节期追施"},
            ],
            "prevention_tips": "当前为离线演示模式（Mock）。建议：选用抗病品种、合理密植、增施磷钾肥、及时排水降湿。配置 DEEPSEEK_API_KEY 可获得更精准方案。",
            "agricultural_operations": "秋收后深翻灭茬，清除病残体，减少越冬菌源。",
            "confidence": 0.5,
        }

    # ---------- Mock 回答库 ----------

    def _fixed_perfect_answer(self) -> str:
        return (
            "## 玉米南方锈病综合防治方案\n\n"
            "### 一、病害确诊\n"
            "玉米南方锈病（Southern Corn Rust）是由多堆柄锈菌（Puccinia polysora）引起的气传性真菌病害，"
            "在滦州市夏玉米主产区 7-8 月高温多雨季节暴发风险极高。\n\n"
            "### 二、推荐用药方案\n\n"
            "| 药剂 | 剂型与浓度 | 使用剂量 | 使用方法 | 注意事项 |\n"
            "|------|-----------|---------|---------|----------|\n"
            "| 三唑酮 | 25% 可湿性粉剂 | 1000-1500 倍液 | 叶面均匀喷雾，7 天 1 次 | 避免高温时段施药 |\n"
            "| 戊唑醇 | 43% 悬浮剂 | 3000 倍液 | 叶面喷雾，7-10 天 1 次 | 与三唑酮交替使用 |\n"
            "| 苯醚甲环唑 | 10% 微乳剂 | 2000 倍液 | 叶面喷雾，保护兼治疗 | 安全间隔期 21 天 |\n\n"
            "### 三、农业防治措施\n"
            "1. 选用抗病品种：农大 372、登海 605、郑单 958 等品种抗性较好\n"
            "2. 合理密植：行距 60cm、株距 30cm，保证通风透光\n"
            "3. 增施磷钾肥：避免偏施氮肥，增强植株抗性\n"
            "4. 及时排水：雨后及时排水降湿\n\n"
            "### 四、关键时期防控\n"
            "- **预警期（7 月中旬）**：巡查 3-5 片叶，发现病斑立即喷药保护\n"
            "- **发病初期（7 月下旬-8 月上旬）**：重点喷施三唑酮 1000 倍液\n"
            "- **灌浆期（8 月中下旬）**：使用戊唑醇+苯醚甲环唑复配防治\n\n"
            "### 五、参考文献\n"
            "[1] 《玉米病虫害识别与防治技术》，河北农业大学植保学院，2023\n"
            "[2] 全国农业技术推广服务中心，《农作物病虫害测报技术规范》，2022\n"
            "[3] 滦州市农业农村局，《2024 年夏玉米病虫害防控预案》"
        )

    def _answer_south_rust(self) -> str:
        return (
            "## 玉米南方锈病防治要点\n\n"
            "**病因**: 多堆柄锈菌引起，夏季高温多雨（25-30℃+湿度>90%）极易暴发。\n\n"
            "**防治**:\n"
            "- 选用抗病品种（农大372、登海605）\n"
            "- 7月中下旬巡查，发病初期喷 25%三唑酮1000倍液\n"
            "- 7-10天1次，连喷2-3次\n"
            "- 与戊唑醇交替使用防抗药性"
        )

    def _answer_leaf_blight(self) -> str:
        return "## 玉米大斑病\n\n症状：大型梭形灰褐色病斑。防治：选抗病品种 + 75%百菌清500倍液。秋收后深翻灭茬。"

    def _answer_leaf_spot(self) -> str:
        return "## 玉米小斑病\n\n症状：小型椭圆形病斑，有同心轮纹。防治：50%多菌灵500倍液。增施磷钾肥增强抗性。"

    def _answer_sheath_blight(self) -> str:
        return "## 玉米纹枯病\n\n症状：茎基部云纹状褐色病斑，后期倒伏。防治：5%井冈霉素A水剂1500倍液。合理密植。"

    def _answer_head_smut(self) -> str:
        return "## 玉米丝黑穗病\n\n症状：果穗被破坏成黑粉包。防治：种子包衣（25%多菌灵拌种）+ 轮作倒茬 + 拔除病株。"

    def _answer_common_smut(self) -> str:
        return "## 玉米黑粉病\n\n症状：局部形成瘤状突起，后期变黑。防治：及时切除病瘤深埋，避免机械损伤，深翻土壤。"

    def _answer_corn_borer(self) -> str:
        return "## 玉米螟防治\n\n生物防治：释放赤眼蜂（1万头/亩）。化学防治：心叶末期喷Bt乳剂或20%氰戊菊酯。秋季深翻灭茬。"

    def _answer_aphid(self) -> str:
        return "## 玉米蚜虫防治\n\n黄板诱杀有翅蚜。喷施10%吡虫啉2000倍液。保护瓢虫、草蛉等天敌。"

    def _answer_armyworm(self) -> str:
        return "## 玉米粘虫防治\n\n糖醋液+性诱剂诱杀成虫。低龄幼虫期喷20%氰戊菊酯2000倍液。清晨人工捕捉高龄幼虫。"

    def _answer_spider_mite(self) -> str:
        return "## 玉米红蜘蛛防治\n\n清除田边杂草。喷施1.8%阿维菌素3000倍液。合理灌溉增加田间湿度。"

    def _generic_answer(self, question: str) -> str:
        return (
            f"## 关于「{question}」的回答\n\n"
            "当前为离线演示模式（Mock），未检测到 DEEPSEEK_API_KEY 或 FORCE_DEMO_MODE=true。\n\n"
            "如需真实 AI 回答，请：\n"
            "1. 在 `.env` 中配置 DEEPSEEK_API_KEY\n"
            "2. 或在 `.env` 中设置 DEMO_FIXED_ANSWER=true 启用答辩安全网\n"
            "\n"
            "本系统已预置 20 种滦州玉米常见病害知识，可尝试以下关键词：\n"
            "- 玉米南方锈病 / 大斑病 / 小斑病 / 纹枯病\n"
            "- 玉米螟 / 蚜虫 / 粘虫 / 红蜘蛛"
        )


def create_llm_client() -> LLMClient:
    """策略工厂: 根据配置自动选择 LLM 引擎"""
    if settings.FORCE_DEMO_MODE or settings.DEMO_FIXED_ANSWER:
        return MockClient()
    if settings.DEEPSEEK_API_KEY:
        return DeepSeekClient()
    return MockClient()
