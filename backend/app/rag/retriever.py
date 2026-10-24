from __future__ import annotations

import json
import os
import pickle
import threading
from typing import Optional, List, Dict, Any

import numpy as np

from ..config import settings
from ..ai.embedding import BGEEmbedder

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

try:
    import jieba
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    jieba = None
    BM25Okapi = None


class HybridRetriever:
    """混合检索引擎：FAISS 向量检索 + BM25 稀疏检索 + Reranker 重排序"""

    _instance: Optional["HybridRetriever"] = None
    _lock = threading.Lock()

    INDEX_FILE = "faiss_index.bin"
    META_FILE = "chunks_meta.pkl"
    BM25_FILE = "bm25.pkl"

    def __init__(self, persist_dir: str, embedder: BGEEmbedder):
        self.persist_dir = persist_dir
        self.embedder = embedder
        self.index = None
        self.chunks_meta: List[Dict[str, Any]] = []
        self.bm25 = None
        self._loaded = False
        self._ensure_dir()

    @classmethod
    def get(cls) -> "HybridRetriever":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    embedder = BGEEmbedder.get(settings.BGE_MODEL_PATH)
                    cls._instance = cls(
                        persist_dir=os.path.join(settings.UPLOAD_DIR, "faiss_store"),
                        embedder=embedder,
                    )
                    cls._instance.load()
        return cls._instance

    def _ensure_dir(self):
        os.makedirs(self.persist_dir, exist_ok=True)

    @property
    def index_path(self) -> str:
        return os.path.join(self.persist_dir, self.INDEX_FILE)

    @property
    def meta_path(self) -> str:
        return os.path.join(self.persist_dir, self.META_FILE)

    @property
    def bm25_path(self) -> str:
        return os.path.join(self.persist_dir, self.BM25_FILE)

    def load(self):
        """从磁盘加载已持久化的索引"""
        if FAISS_AVAILABLE and os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.meta_path, "rb") as f:
                    self.chunks_meta = pickle.load(f)
                print(f"[HybridRetriever] 加载 FAISS 索引: {len(self.chunks_meta)} 个分块")
            except Exception as e:
                print(f"[HybridRetriever] 加载旧 FAISS 索引失败: {e}，将重建")
                self.index = None

        if os.path.exists(self.meta_path) and not self.chunks_meta:
            try:
                with open(self.meta_path, "rb") as f:
                    self.chunks_meta = pickle.load(f)
            except Exception:
                pass

        if os.path.exists(self.bm25_path):
            try:
                with open(self.bm25_path, "rb") as f:
                    self.bm25 = pickle.load(f)
            except Exception:
                self.bm25 = None

        if self.index is None and FAISS_AVAILABLE:
            self._build_empty_index()

        self._loaded = True
        modes = []
        if self.index is not None:
            modes.append("FAISS")
        if self.bm25 is not None:
            modes.append("BM25")
        if not modes:
            modes.append("文本回退")
        print(f"[HybridRetriever] 加载完成 | 分块 {len(self.chunks_meta)} | 模式: {'+'.join(modes)}")

    def _build_empty_index(self):
        if not FAISS_AVAILABLE:
            return
        dim = 1024
        self.index = faiss.IndexFlatIP(dim)
        self.chunks_meta = []

    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """向索引中添加分块"""
        if not chunks:
            return

        texts = [c["text"] for c in chunks]

        if FAISS_AVAILABLE:
            try:
                vectors = self.embedder.embed(texts)
                if self.index is None or len(self.chunks_meta) == 0:
                    dim = vectors.shape[1]
                    self.index = faiss.IndexFlatIP(dim)
                self.index.add(vectors.astype(np.float32))
            except Exception as e:
                print(f"[HybridRetriever] FAISS 向量化失败，跳过向量: {e}")

        for i, c in enumerate(chunks):
            c["vector_offset"] = len(self.chunks_meta) + i
        self.chunks_meta.extend(chunks)

        if BM25_AVAILABLE:
            try:
                tokenized = [list(jieba.cut(t)) for t in [m["text"] for m in self.chunks_meta]]
                self.bm25 = BM25Okapi(tokenized)
            except Exception as e:
                print(f"[HybridRetriever] BM25 构建失败: {e}")

        self._persist()

    def remove_document(self, document_id: int):
        """移除指定文档的所有分块"""
        kept = [c for c in self.chunks_meta if c.get("document_id") != document_id]
        if not kept:
            self._build_empty_index()
            self.bm25 = None
            self.chunks_meta = []
            self._persist()
            return

        self.chunks_meta = kept
        if FAISS_AVAILABLE:
            try:
                vectors = self.embedder.embed([c["text"] for c in kept])
                dim = vectors.shape[1]
                self.index = faiss.IndexFlatIP(dim)
                self.index.add(vectors.astype(np.float32))
            except Exception:
                self.index = None

        if BM25_AVAILABLE:
            try:
                tokenized = [list(jieba.cut(c["text"])) for c in kept]
                self.bm25 = BM25Okapi(tokenized)
            except Exception:
                self.bm25 = None
        self._persist()

    def search(self, query: str, top_k: int = 10, vector_weight: float = 0.6, bm25_weight: float = 0.4) -> List[Dict[str, Any]]:
        """混合检索 —— 无 FAISS/BM25 时回退为关键词匹配"""
        if not self.chunks_meta:
            return []

        results: Dict[int, Dict[str, Any]] = {}

        # ---- 向量检索 ----
        if self.index is not None and FAISS_AVAILABLE:
            try:
                q_vec = self.embedder.embed([query]).astype(np.float32)
                k = min(top_k * 3, len(self.chunks_meta))
                scores_v, indices_v = self.index.search(q_vec, k)
                for score, idx in zip(scores_v[0], indices_v[0]):
                    if idx < 0 or idx >= len(self.chunks_meta):
                        continue
                    results[idx] = {
                        "text": self.chunks_meta[idx]["text"],
                        "vector_score": float(score),
                        "source": self.chunks_meta[idx].get("doc_name", ""),
                        "chunk_id": self.chunks_meta[idx].get("id", ""),
                        "document_id": self.chunks_meta[idx].get("document_id"),
                        "_bm25_score": 0.0,
                    }
            except Exception as e:
                print(f"[HybridRetriever] 向量检索失败: {e}")

        # ---- BM25 检索 ----
        bm25_scores = []
        if self.bm25 is not None and BM25_AVAILABLE:
            try:
                q_tokens = list(jieba.cut(query))
                bm25_scores = self.bm25.get_scores(q_tokens)
                max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
                for i, bs in enumerate(bm25_scores):
                    if i in results:
                        results[i]["_bm25_score"] = float(bs) / max_bm25
                    elif bs > 0:
                        results[i] = {
                            "text": self.chunks_meta[i]["text"],
                            "vector_score": 0.0,
                            "source": self.chunks_meta[i].get("doc_name", ""),
                            "chunk_id": self.chunks_meta[i].get("id", ""),
                            "document_id": self.chunks_meta[i].get("document_id"),
                            "_bm25_score": float(bs) / max_bm25,
                        }
            except Exception:
                pass

        # ---- 无任何索引：关键词回退 ----
        if not results:
            q_lower = query.lower()
            for i, chunk in enumerate(self.chunks_meta):
                text = chunk["text"].lower()
                score = sum(1 for w in q_lower.split() if w in text) / max(len(q_lower.split()), 1)
                if score > 0 or any(kw in text for kw in query[:8].split()):
                    results[i] = {
                        "text": chunk["text"],
                        "vector_score": 0.0,
                        "source": chunk.get("doc_name", ""),
                        "chunk_id": chunk.get("id", ""),
                        "document_id": chunk.get("document_id"),
                        "_bm25_score": score * 0.5,
                    }

        if not results:
            return []

        # ---- 融合分数 ----
        max_vec = max((r.get("vector_score", 0) for r in results.values()), default=1.0) or 1.0
        for r in results.values():
            vec_norm = r.get("vector_score", 0) / max_vec
            r["score"] = vector_weight * vec_norm + bm25_weight * r.get("_bm25_score", 0)
            r.pop("_bm25_score", None)

        ranked = sorted(results.values(), key=lambda x: x["score"], reverse=True)[:top_k]
        return ranked

    def _persist(self):
        if FAISS_AVAILABLE and self.index is not None:
            try:
                faiss.write_index(self.index, self.index_path)
            except Exception as e:
                print(f"[HybridRetriever] FAISS 持久化失败: {e}")

        with open(self.meta_path, "wb") as f:
            pickle.dump(self.chunks_meta, f)

        if self.bm25 is not None:
            with open(self.bm25_path, "wb") as f:
                pickle.dump(self.bm25, f)
