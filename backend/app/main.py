"""
FastAPI 应用入口。挂载全部路由，提供健康检查和全局异常处理。
"""
from __future__ import annotations

import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import engine, Base
from .models import knowledge, recognition, plan, chat  # noqa: F401  确保模型被注册到 Base.metadata

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的生命周期钩子。"""
    logger.info("=" * 60)
    logger.info("基于 RAG 的滦州玉米病害识别与管理系统 启动中...")
    logger.info(f"  DeepSeek: {'云端 API' if settings.DEEPSEEK_API_KEY else '❌ 未配置 → Mock 引擎'}")
    logger.info(f"  Qwen-VL:  {'云端 API' if settings.QWEN_API_KEY else '❌ 未配置 → Mock 引擎'}")
    logger.info(f"  DEMO_FIXED_ANSWER: {settings.DEMO_FIXED_ANSWER}")
    logger.info(f"  FORCE_DEMO_MODE:   {settings.FORCE_DEMO_MODE}")
    logger.info(f"  BGE 设备: {settings.DEVICE}")
    logger.info("=" * 60)

    # 自动建表（只建不存在的，不修改已有表结构）
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表检查完成")
    except Exception as e:
        logger.warning(f"数据库初始化异常（首次启动可忽略）: {e}")

    yield

    logger.info("应用关闭")


app = FastAPI(
    title="滦州玉米病害识别与管理系统 API",
    description="基于 RAG 的农业智能辅助系统 —— 病害识别 / RAG 问答 / 知识库 / 防治方案",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理 —— 返回详细错误信息便于调试"""
    tb = traceback.format_exc()
    logger.error(f"未捕获异常 | {request.method} {request.url.path}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "type": type(exc).__name__,
            "traceback": tb,
        },
    )


@app.get("/api/health", tags=["health"])
async def health_check():
    """全局健康检查 —— 返回 API 版本和 Mock 状态。"""
    return {
        "status": "ok",
        "service": "crop-doctor-backend",
        "version": "1.0.0",
        "force_demo_mode": settings.FORCE_DEMO_MODE,
        "demo_fixed_answer": settings.DEMO_FIXED_ANSWER,
        "deepseek_configured": bool(settings.DEEPSEEK_API_KEY),
        "qwen_configured": bool(settings.QWEN_API_KEY),
    }


@app.get("/api/health/db", tags=["health"])
async def db_health_check():
    """数据库连通性检查。"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}


# ===== 路由注册（导入延迟，避免循环引用）=====
def _register_routers():
    from .api import recognition, chat, knowledge, plan, stats
    app.include_router(recognition.router)
    app.include_router(chat.router)
    app.include_router(knowledge.router)
    app.include_router(plan.router)
    app.include_router(stats.router)


_register_routers()


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
                        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.BACKEND_PORT, reload=True)
