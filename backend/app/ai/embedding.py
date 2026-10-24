from __future__ import annotations

import os
import threading
from typing import Optional, List, Tuple

import numpy as np


class BGEEmbedder:
    """BGE-M3 向量化器 —— 强制 CPU 加载，不占 GPU 显存"""

    _instance: Optional["BGEEmbedder"] = None
    _lock = threading.Lock()

    def __init__(self, model_path: str):
        os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            SentenceTransformer = None

        if SentenceTransformer is None:
            self.model = None
            print("[BGEEmbedder] sentence-transformers 未安装，向量化将返回 Mock 向量")
            return

        if not os.path.exists(model_path):
            self.model = None
            print(f"[BGEEmbedder] 模型路径不存在: {model_path}，向量化将返回 Mock 向量")
            return

        try:
            print(f"[BGEEmbedder] 加载模型: {model_path} (device=cpu)")
            self.model = SentenceTransformer(model_path, device="cpu")
            self.model.max_seq_length = 8192
        except Exception as e:
            self.model = None
            print(f"[BGEEmbedder] 模型加载失败: {e}，向量化将返回 Mock 向量")

    @classmethod
    def get(cls, model_path: str) -> "BGEEmbedder":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(model_path)
        return cls._instance

    def embed(self, texts: List[str]) -> np.ndarray:
        if self.model is None:
            dim = 1024
            rng = np.random.default_rng(hash("|".join(texts)) % (2**31))
            return rng.random((len(texts), dim), dtype=np.float32)
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)


class BGEReranker:
    """BGE-Reranker-v2-m3 重排序器 —— 强制 CPU"""

    _instance: Optional["BGEReranker"] = None
    _lock = threading.Lock()

    def __init__(self, model_path: str):
        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            CrossEncoder = None

        if CrossEncoder is None:
            self.model = None
            print("[BGEReranker] sentence-transformers 未安装，重排序将跳过")
            return

        if not os.path.exists(model_path):
            self.model = None
            print(f"[BGEReranker] 模型路径不存在: {model_path}，重排序将跳过")
            return

        try:
            print(f"[BGEReranker] 加载重排序模型: {model_path} (device=cpu)")
            self.model = CrossEncoder(model_path, device="cpu")
        except Exception as e:
            self.model = None
            print(f"[BGEReranker] 重排序模型加载失败: {e}，重排序将跳过")

    @classmethod
    def get(cls, model_path: str) -> "BGEReranker":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(model_path)
        return cls._instance

    def rerank(self, query: str, candidates: List[str], top_k: int = 5) -> List[Tuple[int, float, str]]:
        """返回 [(index, score, text), ...] 按分数降序"""
        if not candidates:
            return []
        if self.model is None:
            scores = np.random.default_rng(hash(query) % (2**31)).random(len(candidates))
            ranked = sorted(enumerate(zip(scores, candidates)), key=lambda x: x[1][0], reverse=True)
            return [(idx, float(sc), text) for idx, (sc, text) in ranked[:top_k]]

        pairs = [[query, text] for text in candidates]
        scores = self.model.predict(pairs)
        ranked = sorted(enumerate(zip(scores, candidates)), key=lambda x: x[1][0], reverse=True)
        return [(idx, float(sc), text) for idx, (sc, text) in ranked[:top_k]]
