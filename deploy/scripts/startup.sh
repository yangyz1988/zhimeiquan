#!/bin/bash
# =========================================
# 智媒圈 API 后端启动脚本
# 功能：确保数据目录、运行迁移、启动服务
# =========================================
set -e

echo "=== 智媒圈 Backend Startup ==="

# 确保所有 data/ 子目录存在（安全兜底）
echo "→ 确保数据目录存在..."
mkdir -p /app/data/{rules,analytics,scheduled,agents,templates,ab_tests,teams,videos,images,competitors,calibration,rewrites,router_history,insights,workflows}

# 种子平台规则（如果 rules/ 为空）
if [ -z "$(ls -A /app/data/rules 2>/dev/null)" ]; then
    echo "→ 初始化种子平台规则..."
    python -c "
from monitors.scheduler import RuleScheduler
try:
    sched = RuleScheduler(data_dir='/app/data/rules')
    sched.seed_rules()
    print('  种子规则写入完成')
except Exception as e:
    print(f'  [警告] 种子规则初始化跳过: {e}')
" || echo "  [警告] 种子规则初始化失败（可稍后手动执行）"
fi

# 后端服务健康检查端点已在 main.py 中注册
# 启动 uvicorn 服务
echo "→ 启动 Uvicorn 服务器..."
echo "  监听地址: 0.0.0.0:8000"
echo "  工作进程: ${UVICORN_WORKERS:-4}"
echo "  日志级别: ${LOG_LEVEL:-info}"
echo ""

exec uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${UVICORN_WORKERS:-4}" \
    --log-level "${LOG_LEVEL,,:-info}"
