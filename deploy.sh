#!/usr/bin/env bash
# 智媒圈 一键部署脚本
# 用法: ./deploy.sh [vercel|docker|railway|all]

set -e

cd "$(dirname "$0")"

ACTION="${1:-docker}"

echo "=== 智媒圈部署: $ACTION ==="

case "$ACTION" in
  docker)
    echo "→ 选择配置文件..."
    if [ -n "$PROD" ] || [ "${2:-}" = "prod" ]; then
      COMPOSE_FILE="-f docker-compose.prod.yml"
      echo "  使用生产配置 (docker-compose.prod.yml)"
    else
      COMPOSE_FILE="-f docker-compose.yml"
      echo "  使用开发配置 (docker-compose.yml)"
    fi

    echo "→ 检查 .env 文件..."
    if [ ! -f .env ]; then
      if [ -n "$PROD" ] || [ "${2:-}" = "prod" ]; then
        cp .env.production.example .env
      else
        cp .env.example .env
      fi
      echo "  ⚠️  已生成 .env，请填写密钥后重新运行"
      exit 1
    fi

    echo "→ 构建镜像..."
    docker compose $COMPOSE_FILE build

    echo "→ 启动服务..."
    docker compose $COMPOSE_FILE up -d

    echo "→ 等待健康检查..."
    sleep 15

    echo "→ 验证服务..."
    curl -sf http://localhost:3000 > /dev/null && echo "  ✓ SaaS (3000) OK" || echo "  ✗ SaaS 启动失败"
    curl -sf http://localhost:8000/health > /dev/null && echo "  ✓ API (8000) OK" || echo "  ✗ API 启动失败"
    curl -sf http://localhost:80 > /dev/null && echo "  ✓ Nginx (80) OK" || echo "  ✗ Nginx 启动失败"

    echo ""
    echo "部署完成！访问 http://localhost"
    echo "生产模式: 访问 https://your-domain.com"
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
    echo "用法: $0 [docker|docker prod|vercel|railway|all]"
    echo "   docker      使用 docker-compose.yml 启动开发环境"
    echo "   docker prod 使用 docker-compose.prod.yml 启动生产环境"
    echo "   vercel      部署前端到 Vercel"
    echo "   railway     部署后端到 Railway"
    echo "   all         同时部署 Vercel + Railway"
    exit 1
    ;;
esac
