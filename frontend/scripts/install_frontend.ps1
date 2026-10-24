$ErrorActionPreference = "Continue"
$FrontendDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  滦州玉米病害系统 — 前端安装脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Push-Location $FrontendDir
try {
    Write-Host "[1/2] npm install..." -ForegroundColor Green
    npm.cmd install
    if ($LASTEXITCODE -ne 0) { Write-Host "npm install 失败！" -ForegroundColor Red; exit 1 }
    Write-Host "npm install ✅" -ForegroundColor Green

    Write-Host ""
    Write-Host "[2/2] 验证..." -ForegroundColor Green
    if (Test-Path "node_modules") {
        Write-Host "  node_modules 已创建 ✅" -ForegroundColor Green
    } else {
        Write-Host "  node_modules 不存在 ❌" -ForegroundColor Red; exit 1
    }
} finally { Pop-Location }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🎉 前端安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "  启动前端开发服务器：" -ForegroundColor White
Write-Host "    cd d:\bs\frontend" -ForegroundColor White
Write-Host "    npm.cmd run dev" -ForegroundColor White
Write-Host ""
Write-Host "  默认地址：http://localhost:5173" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
