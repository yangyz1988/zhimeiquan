-- ========================================
-- 智媒圈 PostgreSQL 初始化脚本
-- ========================================

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- 文本搜索优化

-- 设置时区
SET TIME ZONE 'Asia/Shanghai';

-- 授权
GRANT ALL PRIVILEGES ON DATABASE zhimeiquan TO zhimeiquan;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO zhimeiquan;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO zhimeiquan;

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Prisma 会自动创建表，这里只做初始化
-- 生产环境建议使用 Prisma Migrate
