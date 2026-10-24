"""
应用配置模块 —— 使用 pydantic-settings 从 .env 加载配置。
MySQL 不可用时自动降级为 SQLite（零依赖）。
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """全局配置类，字段自动从环境变量或 .env 文件中读取。"""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DB_HOST: str = ""
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root123"
    DB_NAME: str = "crop_doctor"
    DB_CHARSET: str = "utf8mb4"

    REDIS_HOST: str = ""
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

    QWEN_API_KEY: str = ""
    QWEN_VL_MODEL: str = "qwen-vl-max"

    DEMO_FIXED_ANSWER: bool = False
    FORCE_DEMO_MODE: bool = False

    BGE_MODEL_PATH: str = str(BASE_DIR / "models" / "bge-m3")
    RERANKER_MODEL_PATH: str = str(BASE_DIR / "models" / "bge-reranker")
    DEVICE: str = "cpu"

    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    FAISS_INDEX_DIR: str = str(BASE_DIR / "models" / "faiss_index")

    BACKEND_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    @property
    def database_url(self) -> str:
        if self.DB_HOST:
            return (
                f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
                f"?charset={self.DB_CHARSET}"
            )
        sqlite_path = BASE_DIR / "crop_doctor.db"
        return f"sqlite:///{sqlite_path}"

    @property
    def using_sqlite(self) -> bool:
        return not bool(self.DB_HOST)

    @property
    def redis_url(self) -> str:
        if not self.REDIS_HOST:
            return ""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
