#!/bin/bash
# ========================================
# 智媒圈生产部署脚本
# ========================================

set -e

echo "========================================"
echo "智媒圈生产环境部署"
echo "========================================"

# 检查环境变量
if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "错误: POSTGRES_PASSWORD 未设置"
    exit 1
fi

if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "错误: DEEPSEEK_API_KEY 未设置"
    exit 1
fi

# 创建必要的目录
mkdir -p data deploy/nginx/logs deploy/nginx/ssl

# 拉取最新代码
echo ">>> 拉取最新代码..."
git pull origin master

# 构建镜像
echo ">>> 构建 Docker 镜像..."
docker compose -f docker-compose.prod.yml build --no-cache

# 数据库迁移
echo ">>> 运行数据库迁移..."
cd saas && npx prisma generate && npx prisma migrate deploy && cd ..

# 停止旧容器
echo ">>> 停止旧容器..."
docker compose -f docker-compose.prod.yml down --remove-orphans

# 启动新容器
echo ">>> 启动新容器..."
docker compose -f docker-compose.prod.yml up -d

# 健康检查
echo ">>> 等待服务启动..."
sleep 10

echo ">>> 健康检查..."
curl -f http://localhost:8000/health || {
    echo "API 健康检查失败"
    docker compose -f docker-compose.prod.yml logs api
    exit 1
}

curl -f http://localhost:3000/api/health || {
    echo "前端健康检查失败"
    docker compose -f docker-compose.prod.yml logs saas
    exit 1
}

echo "========================================"
echo "部署完成!"
echo "========================================"
echo "前端: https://www.zhimeiquan.com"
echo "API:  https://api.zhimeiquan.com"
echo "========================================"