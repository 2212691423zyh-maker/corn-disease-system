"""重建知识库表结构（修复 SQLite 下 BigInteger 主键不自增问题）"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models import knowledge, recognition, plan, chat, disease  # noqa

from sqlalchemy import text

TABLES_TO_RECREATE = [
    "knowledge_chunks",
    "document_versions",
    "knowledge_documents",
]

with engine.begin() as conn:
    for tbl in TABLES_TO_RECREATE:
        conn.execute(text(f"DROP TABLE IF EXISTS {tbl}"))
        print(f"dropped {tbl}")

Base.metadata.create_all(bind=engine)
print("tables recreated OK")

from sqlalchemy import inspect
insp = inspect(engine)
print("current tables:", insp.get_table_names())
