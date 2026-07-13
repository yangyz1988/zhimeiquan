#!/bin/bash
# ========================================
# 数据库备份脚本
# ========================================

set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/zhimeiquan_$DATE.sql.gz"

# 创建备份目录
mkdir -p $BACKUP_DIR

echo ">>> 开始备份数据库..."

# 执行备份
docker exec zhimeiquan-postgres pg_dump -U zhimeiquan zhimeiquan | gzip > $BACKUP_FILE

echo ">>> 备份完成: $BACKUP_FILE"

# 清理旧备份（保留30天）
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo ">>> 清理完成"