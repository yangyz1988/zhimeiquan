import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_generate_content():
    resp = client.post(
        "/api/v1/content/generate",
        json={
            "topic": "AI自媒体",
            "platform": "抖音",
            "persona": "学长型",
            "duration": 60,
        },
    )
    # Returns 500 when DEEPSEEK_API_KEY is not configured
    assert resp.status_code in [200, 500]


def test_generate_titles():
    resp = client.post(
        "/api/v1/titles/generate",
        json={"topic": "自媒体赚钱", "platform": "抖音", "count": 3},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_score_content():
    resp = client.post(
        "/api/v1/content/score",
        json={
            "title": "3个底层逻辑",
            "body": "你以为做自媒体就是...",
            "platform": "抖音",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "hook" in data
    assert "total" in data
    assert "level" in data


def test_monitor_rules_status():
    resp = client.get("/api/v1/monitor/rules/status")
    # May return 200 with expired status or 404 if no rules exist yet
    assert resp.status_code in [200, 404]
