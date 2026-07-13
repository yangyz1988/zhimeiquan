#!/bin/bash
# ========================================
# SSL 证书配置脚本 (Let's Encrypt)
# ========================================

set -e

DOMAIN="zhimeiquan.com"
EMAIL="admin@zhimeiquan.com"

echo "========================================"
echo "SSL 证书配置"
echo "========================================"

# 检查 certbot
if ! command -v certbot &> /dev/null; then
    echo "安装 certbot..."
    apt-get update && apt-get install -y certbot
fi

# 停止 nginx 以释放 80 端口
docker compose -f docker-compose.prod.yml stop nginx || true

# 获取证书
echo "获取证书..."
certbot certonly --standalone \
    -d www.zhimeiquan.com \
    -d zhimeiquan.com \
    -d api.zhimeiquan.com \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --keep

# 复制证书到 nginx 目录
echo "复制证书..."
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem deploy/nginx/ssl/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem deploy/nginx/ssl/
chmod 644 deploy/nginx/ssl/*

# 重启 nginx
docker compose -f docker-compose.prod.yml start nginx

echo "========================================"
echo "SSL 配置完成"
echo "========================================"