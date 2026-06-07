#!/usr/bin/env bash
# 智媒圈 一键部署脚本
# 用法: ./deploy.sh [vercel|docker|railway|all]

set -e

cd "$(dirname "$0")"

ACTION="${1:-docker}"

echo "=== 智媒圈部署: $ACTION ==="

case "$ACTION" in
  docker)
    echo "→ 检查 .env 文件..."
    if [ ! -f .env ]; then
      cp .env.production.example .env
      echo "  ⚠️  已生成 .env，请填写密钥后重新运行"
      exit 1
    fi

    echo "→ 构建镜像..."
    docker compose build

    echo "→ 启动服务..."
    docker compose up -d

    echo "→ 等待健康检查..."
    sleep 15

    echo "→ 验证服务..."
    curl -sf http://localhost:3000 > /dev/null && echo "  ✓ SaaS (3000) OK" || echo "  ✗ SaaS 启动失败"
    curl -sf http://localhost:8000/health > /dev/null && echo "  ✓ API (8000) OK" || echo "  ✗ API 启动失败"
    curl -sf http://localhost:6379 > /dev/null && echo "  ✓ Redis (6379) OK" || echo "  ✗ Redis 启动失败"

    echo ""
    echo "部署完成！访问 http://localhost"
    ;;

  vercel)
    echo "→ 部署前端到 Vercel..."
    cd saas
    if ! command -v vercel &> /dev/null; then
      echo "  请先安装: npm i -g vercel"
      exit 1
    fi
    vercel --prod
    cd ..
    ;;

  railway)
    echo "→ 部署后端到 Railway..."
    if ! command -v railway &> /dev/null; then
      echo "  请先安装: npm i -g @railway/cli"
      exit 1
    fi
    railway up
    ;;

  all)
    echo "→ 部署到 Vercel + Railway..."
    bash deploy.sh vercel
    bash deploy.sh railway
    ;;

  *)
    echo "用法: $0 [docker|vercel|railway|all]"
    exit 1
    ;;
esac
