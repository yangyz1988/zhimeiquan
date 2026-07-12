# 生产部署检查清单

## 已完成的安全修复

### P0 严重问题（已修复）
- [x] **竞品监控 API 缺少认证** - scripts/routers/competitors.py
  - 所有端点添加 _get_auth_user() 认证验证
  - 强制使用认证用户 ID

- [x] **支付系统用户 ID 可伪造** - scripts/routers/payment.py
  - 生产环境强制使用认证用户
  - 禁止使用请求体中的 user_id

- [x] **模型路由器代码错误** - scripts/services/router.py
  - 修复 per_task 未定义错误
  - 添加缺失的 _load_history() 方法
  - 添加缺失的 select_model() 方法

### P1 高风险问题（已修复）
- [x] **Stripe webhook 处理不完整** - scripts/services/payment.py
  - 添加 handle_subscription_updated_from_checkout() 方法
  - 添加 cancel_user_subscription() 方法

- [x] **Prompt 注入风险** - scripts/services/validators.py
  - 添加 sanitize_for_llm() 函数
  - 添加 safe_json_escape() 函数

---

## 生产部署前检查

### 环境变量检查
`.env
# 必需变量（缺失将导致服务不可用）
DEEPSEEK_API_KEY=sk-your-key-here
DATABASE_URL=postgresql://user:pass@host:5432/zhimeiquan
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxx
CLERK_SECRET_KEY=sk_live_xxx

# 强烈推荐
API_SECRET=<强密码，32位以上随机字符串>
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# 生产环境标识（启用严格认证）
ENV=production
`

### 安全检查清单
- [x] .env 已被 .gitignore 忽略
- [x] .env 从未提交到 git 历史
- [x] 无硬编码密钥在代码中
- [x] 认证中间件已启用
- [x] CORS 已限制为生产域名
- [x] 速率限制已启用

### 数据库检查
- [ ] PostgreSQL 已配置（生产建议）
- [ ] 数据库迁移已执行 pnpm db:migrate
- [ ] 数据库备份策略已就绪

### Docker 检查
- [ ] docker-compose.prod.yml 配置正确
- [ ] 健康检查端点可用 /health, /ready
- [ ] 日志配置已启用

### 监控检查
- [ ] 日志收集已配置
- [ ] 错误追踪已启用
- [ ] 性能监控已就绪

---

## 提交记录

`
d9c7b9a fix(security): critical security vulnerabilities patched
`

---

## 下一步

1. 推送到远程仓库：git push origin master
2. 触发 CI/CD 流程
3. 验证测试通过
4. 部署到生产环境
5. 执行冒烟测试

---

生成时间: 2026-07-12 10:33:10
