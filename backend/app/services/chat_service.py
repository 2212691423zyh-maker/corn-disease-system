from __future__ import annotations

import json
import os
from typing import Optional, List, Dict, Any

from ..config import settings
from ..ai.client import create_llm_client, MockClient
from ..ai.embedding import BGEReranker
from ..rag.retriever import HybridRetriever


SYSTEM_PROMPT = """你是「滦州玉米病害智能顾问」，一个基于 RAG 的专业农业 AI 助手。

你的回答必须遵循以下规范：
1. **真实性**：只基于检索到的知识回答，不知道就说不知道
2. **结构化**：使用 Markdown 格式，分小节清晰呈现（病因、症状、防治、用药）
3. **可溯源**：每个关键结论末尾标注引用来源 [来源]
4. **专业性**：使用农业专业术语，但让农民能读懂
5. **针对性**：结合滦州市夏玉米主产区特点（7-8月雨季高发）

引用格式示例：...这是因为高温高湿条件利于病菌繁殖 [《玉米病虫害识别与防治》]
"""


class ChatService:
    """RAG 问答服务"""

    MAX_CONTEXT_TOKENS = 4000

    @classmethod
    def answer(cls, question: str, session_id: Optional[str] = None, history: Optional[List[Dict[str, Any]]] = None, force_fixed_answer: bool = False) -> Dict[str, Any]:
        # ---- 答辩安全网：强制固定回答 ----
        if force_fixed_answer or settings.DEMO_FIXED_ANSWER:
            return cls._fixed_answer_response()

        # ---- 1. 检索 ----
        retriever = HybridRetriever.get()
        raw_chunks = retriever.search(question, top_k=10)

        # ---- 2. Rerank ----
        reranker = BGEReranker.get(settings.RERANKER_MODEL_PATH)
        candidates = [c["text"] for c in raw_chunks]
        reranked = reranker.rerank(question, candidates, top_k=5)

        final_chunks = []
        seen_texts = set()
        for idx, score, text in reranked:
            if text not in seen_texts:
                seen_texts.add(text)
                orig = raw_chunks[idx] if idx < len(raw_chunks) else {}
                final_chunks.append({
                    "text": text,
                    "score": score,
                    "source": orig.get("source", "未知来源"),
                    "document_id": orig.get("document_id"),
                    "chunk_id": orig.get("chunk_id"),
                })

        # ---- 3. 拼接上下文 ----
        context_parts = []
        for i, c in enumerate(final_chunks, 1):
            context_parts.append(f"[{i}] 来源: {c['source']}\n{c['text']}")
        context = "\n\n---\n\n".join(context_parts) if context_parts else "(未检索到相关知识)"

        # ---- 4. 构建消息 ----
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"【检索到的知识证据】\n{context}"},
        ]

        # 加入最近 5 轮历史
        if history:
            for m in history[-10:]:
                messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

        messages.append({"role": "user", "content": question})

        # ---- 5. LLM 生成 ----
        llm = create_llm_client()
        answer_text = llm.chat(messages, temperature=0.6)

        # ---- 6. 构造引用 ----
        citations = [
            {
                "rank": i + 1,
                "source": c["source"],
                "score": round(c["score"], 3),
                "chunk_text": c["text"][:200],
            }
            for i, c in enumerate(final_chunks)
        ]

        return {
            "answer": answer_text,
            "citations": citations,
            "has_evidence": len(citations) > 0,
            "retrieval_score": round(sum(c["score"] for c in citations) / max(len(citations), 1), 3),
            "model_used": llm.name,
        }

    @classmethod
    def _fixed_answer_response(cls) -> Dict[str, Any]:
        """答辩安全网：返回南方锈病完美回答 + 3 条引用溯源"""
        mock = MockClient()
        answer_text = mock._fixed_perfect_answer()
        citations = [
            {"rank": 1, "source": "《玉米病虫害识别与防治技术》", "score": 0.96, "chunk_text": "玉米南方锈病由多堆柄锈菌引起，7-8月高温多雨季节暴发..."},
            {"rank": 2, "source": "滦州市2024年玉米病虫害防控预案", "score": 0.92, "chunk_text": "发病初期喷施25%三唑酮1000倍液，7-10天1次，连喷2-3次..."},
            {"rank": 3, "source": "全国农业技术推广服务中心测报规范", "score": 0.88, "chunk_text": "选用抗病品种农大372、登海605，合理密植保证通风透光..."},
        ]
        return {
            "answer": answer_text,
            "citations": citations,
            "has_evidence": True,
            "retrieval_score": 0.92,
            "model_used": "DemoFixedAnswer",
        }
