"""Grafana 仪表盘配置"""
# 此文件提供 Grafana Dashboard JSON 配置
# 导入方法: Grafana -> Dashboards -> Import -> paste JSON

DASHBOARD_JSON = """
{
  "annotations": {
    "list": []
  },
  "title": "智媒圈监控仪表盘",
  "uid": "zhimeiquan-main",
  "version": 1,
  "schemaVersion": 38,
  "refresh": "30s",
  "tags": ["zhimeiquan", "api", "production"],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "panels": [
    {
      "title": "请求速率",
      "type": "graph",
      "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
      "targets": [
        {
          "expr": "sum(rate(http_requests_total[5m]))",
          "legendFormat": "请求/秒"
        }
      ]
    },
    {
      "title": "响应延迟 (P95)",
      "type": "graph",
      "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
          "legendFormat": "P95 延迟"
        }
      ]
    },
    {
      "title": "错误率",
      "type": "graph",
      "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
      "targets": [
        {
          "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
          "legendFormat": "错误率"
        }
      ]
    },
    {
      "title": "活跃连接",
      "type": "stat",
      "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
      "targets": [
        {
          "expr": "active_connections",
          "legendFormat": "连接数"
        }
      ]
    },
    {
      "title": "缓存命中率",
      "type": "gauge",
      "gridPos": {"h": 8, "w": 8, "x": 0, "y": 16},
      "targets": [
        {
          "expr": "sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))",
          "legendFormat": "命中率"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "max": 1,
          "min": 0,
          "unit": "percentunit"
        }
      }
    },
    {
      "title": "数据库查询延迟",
      "type": "graph",
      "gridPos": {"h": 8, "w": 8, "x": 8, "y": 16},
      "targets": [
        {
          "expr": "histogram_quantile(0.95, sum(rate(db_query_duration_seconds_bucket[5m])) by (le))",
          "legendFormat": "P95 查询延迟"
        }
      ]
    },
    {
      "title": "用户统计",
      "type": "stat",
      "gridPos": {"h": 8, "w": 8, "x": 16, "y": 16},
      "targets": [
        {
          "expr": "user_total",
          "legendFormat": "总用户"
        },
        {
          "expr": "user_active_total",
          "legendFormat": "活跃用户"
        }
      ]
    },
    {
      "title": "内容发布趋势",
      "type": "graph",
      "gridPos": {"h": 8, "w": 12, "x": 0, "y": 24},
      "targets": [
        {
          "expr": "increase(content_published_total[1h])",
          "legendFormat": "每小时发布"
        }
      ]
    },
    {
      "title": "订阅收入",
      "type": "stat",
      "gridPos": {"h": 8, "w": 12, "x": 12, "y": 24},
      "targets": [
        {
          "expr": "sum(increase(subscription_revenue_total[24h]))",
          "legendFormat": "24h 收入 (分)"
        }
      ]
    }
  ]
}
"""

# Prometheus 配置
PROMETHEUS_CONFIG = """
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - /etc/prometheus/alerts.yml

scrape_configs:
  - job_name: 'zhimeiquan-api'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
"""

# 告警规则
ALERT_RULES = """
groups:
  - name: zhimeiquan-alerts
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "高错误率"
          description: "错误率超过 5%，当前: {{ $value | humanizePercentage }}"

      - alert: HighLatency
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "高延迟"
          description: "P95 延迟超过 2 秒"

      - alert: ServiceDown
        expr: up{job="zhimeiquan-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "服务下线"
          description: "API 服务不可用"

      - alert: LowCacheHitRate
        expr: sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m]))) < 0.7
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "低缓存命中率"
          description: "缓存命中率低于 70%"
"""

# 告警管理器配置
ALERTMANAGER_CONFIG = """
global:
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@zhimeiquan.com'
  smtp_auth_username: 'alerts@zhimeiquan.com'
  smtp_auth_password: 'password'

route:
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'team-email'
  
receivers:
  - name: 'team-email'
    email_configs:
      - to: 'team@zhimeiquan.com'
        send_resolved: true

  - name: 'team-slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        send_resolved: true
"""

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "dashboard":
            print(DASHBOARD_JSON)
        elif sys.argv[1] == "prometheus":
            print(PROMETHEUS_CONFIG)
        elif sys.argv[1] == "alerts":
            print(ALERT_RULES)
        elif sys.argv[1] == "alertmanager":
            print(ALERTMANAGER_CONFIG)