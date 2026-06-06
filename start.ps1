# 智媒圈快速启动脚本
param(
    [switch]$Docker
)

Write-Host "=== 智媒圈 AI自媒体内容工厂 ===" -ForegroundColor Cyan

if ($Docker) {
    Write-Host "使用 Docker Compose 启动..." -ForegroundColor Yellow
    docker compose up -d
    Write-Host "服务已启动:" -ForegroundColor Green
    Write-Host "  Next.js: http://localhost:3000"
    Write-Host "  API:     http://localhost:8000/docs"
} else {
    Write-Host "本地开发模式启动..." -ForegroundColor Yellow

    # 检查 .env
    if (-not (Test-Path ".env")) {
        Write-Host "未找到 .env，从 .env.example 复制..." -ForegroundColor Yellow
        Copy-Item .env.example .env
        Write-Host "请编辑 .env 填入 DEEPSEEK_API_KEY" -ForegroundColor Red
    }

    # 启动 Next.js
    Write-Host "启动 Next.js..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd saas; pnpm install; pnpm dev"

    # 启动 Python API
    Write-Host "启动 Python API..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd scripts; pip install -r requirements.txt; uvicorn main:app --reload --port 8000"

    Write-Host "服务启动中..." -ForegroundColor Green
    Write-Host "  Next.js: http://localhost:3000"
    Write-Host "  API:     http://localhost:8000/docs"
}
