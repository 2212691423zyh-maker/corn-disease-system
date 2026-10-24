# 后端依赖安装说明

## 一键安装

在项目根目录（非 Trae 沙箱）打开 PowerShell，执行：

```powershell
# 使用 Anaconda Python 3.11（已预装 numpy、scipy、pandas 等）
powershell -ExecutionPolicy Bypass -File backend\scripts\install_backend.ps1
```

该脚本会自动完成三件事：
1. 安装全部 Python 依赖（fastapi、uvicorn、sqlalchemy2.x、faiss-cpu、sentence-transformers 等）
2. 从 ModelScope（国内镜像）下载 BGE-M3 和 BGE-Reranker-v2-m3 到 `backend/models/`
3. 验证 FastAPI 骨架能正常 import

## 手动安装（如果脚本有问题）

```powershell
# 1. 安装依赖
C:\a\python.exe -m pip install -r backend\requirements.txt

# 2. 下载模型（ModelScope）
pip install modelscope
C:\a\python.exe -m modelscope download --model BAAI/bge-m3 --local_dir backend\models\bge-m3
C:\a\python.exe -m modelscope download --model BAAI/bge-reranker-v2-m3 --local_dir backend\models\bge-reranker

# 3. 验证
cd backend
C:\a\python.exe -c "from app.main import app; print('OK')"
```

## 备选：HuggingFace 下载模型

如果 ModelScope 也不行，换 HuggingFace：

```powershell
C:\a\python.exe -m pip install huggingface_hub
C:\a\python.exe -c "from huggingface_hub import snapshot_download; snapshot_download('BAAI/bge-m3', local_dir='backend/models/bge-m3')"
C:\a\python.exe -c "from huggingface_hub import snapshot_download; snapshot_download('BAAI/bge-reranker-v2-m3', local_dir='backend/models/bge-reranker')"
```

## 环境变量

复制 `backend/.env.example` 为 `backend/.env`，按需填写：

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek 云端 API Key。**不填则自动降级为 Mock 引擎** |
| `QWEN_API_KEY` | Qwen-VL 云端 API Key（阿里云 DashScope）。**不填则自动降级为 Mock** |
| `DEMO_FIXED_ANSWER` | `true/false`。`true` 时所有 RAG 问答固定返回"南方锈病完美回答"，答辩断网安全网 |
| `FORCE_DEMO_MODE` | `true/false`。`true` 时完全不调用任何云端 API |
| `DB_HOST/PORT/USER/PASSWORD/NAME` | MySQL 连接信息 |
| `BGE_MODEL_PATH` / `RERANKER_MODEL_PATH` | 模型路径。默认 `./models/bge-m3` / `./models/bge-reranker` |
| `DEVICE` | 固定 `cpu`，BGE 模型强制 CPU 加载 |
