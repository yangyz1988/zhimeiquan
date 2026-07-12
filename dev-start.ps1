# 智媒圈 开发环境启动脚本
# 使用方法: .\dev-start.ps1

Write-Host "
=== 智媒圈 ZhiMeiQuan 开发环境 ===" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# 检查 Python
try {
    $result = $(python --version 2>&1)
    Write-Host "[OK] Python: $result" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] 请先安装 Python 3.10+" -ForegroundColor Red
    exit 1
}

# 检查 Node.js
try {
    $result = $(node --version 2>&1)
    Write-Host "[OK] Node.js: $result" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] 请先安装 Node.js 18+" -ForegroundColor Red
    exit 1
}

# 安装 Python 依赖
Write-Host "
[1/4] 安装 Python 依赖..." -ForegroundColor Yellow
Set-Location scripts
if (-not (Test-Path "venv")) {
    python -m venv venv
}
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt -q
Set-Location ..

# 安装前端依赖
Write-Host "[2/4] 安装前端依赖..." -ForegroundColor Yellow
Set-Location saas
if (-not (Test-Path "node_modules")) {
    pnpm install
}
pnpm db:generate
Set-Location ..

# 初始化数据库
Write-Host "[3/4] 初始化数据库..." -ForegroundColor Yellow
Set-Location saas
pnpm db:push
Set-Location ..

# 启动服务
Write-Host "
[4/4] 启动开发服务..." -ForegroundColor Yellow
Write-Host "
打开两个终端窗口:" -ForegroundColor Cyan
Write-Host "  终端1 (后端): cd scripts; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host "  终端2 (前端): cd saas; pnpm dev" -ForegroundColor White
Write-Host "
访问: http://localhost:3000" -ForegroundColor Green
Write-Host "API文档: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "数据库管理: cd saas; pnpm db:studio" -ForegroundColor Green
Write-Host "
==================================" -ForegroundColor Cyan
