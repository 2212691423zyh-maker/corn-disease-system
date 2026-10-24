$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Split-Path -Parent $ScriptDir
$TargetDir = Join-Path $BackendDir "models"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  滦州玉米病害系统 — 后端安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$PythonExe = "C:\a\python.exe"
if (-not (Test-Path $PythonExe)) { $PythonExe = "python" }
Write-Host "Python: $PythonExe" -ForegroundColor Yellow
& $PythonExe --version

# ===== Step 1: 核心依赖（必须，秒装）=====
Write-Host ""
Write-Host "[1/4] 安装核心依赖..." -ForegroundColor Green
$corePkgs = @(
    "fastapi==0.115.0",
    "uvicorn[standard]==0.30.6",
    "sqlalchemy==2.0.35",
    "pydantic==2.9.2",
    "pydantic-settings==2.5.2",
    "python-multipart",
    "httpx",
    "python-docx",
    "jieba",
    "rank_bm25",
    "numpy",
    "PyMuPDF",
    "pypdf"
)
& $PythonExe -m pip install @corePkgs
if ($LASTEXITCODE -ne 0) { Write-Host "核心依赖安装失败！" -ForegroundColor Red; exit 1 }
Write-Host "核心依赖 ✅" -ForegroundColor Green

# ===== Step 2: 可选大依赖（faiss-cpu / sentence-transformers / modelscope）=====
Write-Host ""
$bigDeps = Read-Host "是否安装大模型依赖（faiss-cpu + sentence-transformers + modelscope）? [y/N]"
if ($bigDeps -eq "y" -or $bigDeps -eq "Y") {
    Write-Host "[2/4] 安装大依赖（较慢）..." -ForegroundColor Green
    & $PythonExe -m pip install faiss-cpu==1.8.0 "sentence-transformers==3.0.1" modelscope==1.18.0
    if ($LASTEXITCODE -ne 0) { Write-Host "大依赖安装失败，将以 Mock 模式运行。" -ForegroundColor Yellow }
} else {
    Write-Host "[2/4] 跳过大依赖（后端将以 Mock 向量运行）" -ForegroundColor DarkGray
}

# ===== Step 3: 下载 BGE 模型（仅装了 modelscope 时）=====
Write-Host ""
$download = Read-Host "是否下载 BGE 模型（向量化 + 重排序）? [y/N]"
if ($download -eq "y" -or $download -eq "Y") {
    if (-not (Test-Path (Join-Path $TargetDir "bge-m3"))) {
        Write-Host "  下载 BGE-M3..." -ForegroundColor Yellow
        & $PythonExe -m modelscope download --model BAAI/bge-m3 --local_dir (Join-Path $TargetDir "bge-m3")
    } else { Write-Host "  BGE-M3 已存在，跳过。" -ForegroundColor DarkGray }

    if (-not (Test-Path (Join-Path $TargetDir "bge-reranker"))) {
        Write-Host "  下载 BGE-Reranker..." -ForegroundColor Yellow
        & $PythonExe -m modelscope download --model BAAI/bge-reranker-v2-m3 --local_dir (Join-Path $TargetDir "bge-reranker")
    } else { Write-Host "  BGE-Reranker 已存在，跳过。" -ForegroundColor DarkGray }
} else {
    Write-Host "[3/4] 跳过模型下载（向量化将使用 Mock）" -ForegroundColor DarkGray
}

# ===== Step 4: 验证 =====
Write-Host ""
Write-Host "[4/4] 验证 FastAPI 骨架..." -ForegroundColor Green
Push-Location $BackendDir
try {
    $out = & $PythonExe -c "from app.main import app; print('骨架验证通过！'); print('可用路由:', [r.path for r in app.routes])" 2>&1
    Write-Host $out
    if ($LASTEXITCODE -ne 0) { Write-Host "⚠️  骨架验证失败，请检查上方报错。" -ForegroundColor Yellow }
} finally { Pop-Location }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🎉 后端安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "  启动后端（SQLite 自动降级模式）：" -ForegroundColor White
Write-Host "    cd d:\bs\backend" -ForegroundColor White
Write-Host "    C:\a\python.exe -m app.main" -ForegroundColor White
Write-Host ""
Write-Host "  如需 MySQL/Redis（可选）：" -ForegroundColor White
Write-Host "    cd d:\bs; docker compose up -d mysql redis" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
