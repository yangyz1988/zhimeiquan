#!/bin/bash
# 启动时运行 Prisma 迁移
# 在 docker-compose 的 init 容器中执行

set -e

echo "=== Prisma Migration 初始化 ==="

cd /app/saas

# 检查 node_modules 和 prisma 客户端
if [ ! -d "node_modules" ]; then
    echo "正在安装依赖..."
    npm install --production
fi

# 生成 Prisma 客户端
echo "正在生成 Prisma 客户端..."
npx prisma generate

# 执行迁移
echo "正在执行数据库迁移..."
npx prisma migrate deploy

# 可选：同步数据库 schema（用于已有数据库的增量更新）
echo "正在同步数据库 Schema..."
npx prisma db push --accept-data-loss || true

echo "=== Prisma 迁移完成 ==="
