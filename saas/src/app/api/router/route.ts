import { NextRequest, NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

/**
 * 模型路由 API 代理
 * 转发请求到后端 /api/v1/router/* 端点
 */

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const pathname = searchParams.get("_pathname") || "";
  const action = searchParams.get("_action");

  try {
    if (action === "profiles") {
      const { ok, status, data } = await apiFetch("/api/v1/router/profiles", {
        cache: "no-store",
      });
      if (!ok) {
        return NextResponse.json({ error: "获取模型档案失败" }, { status });
      }
      return NextResponse.json(data);
    }

    if (action === "recommend") {
      const taskType = searchParams.get("task_type") || "content_generation";
      const priority = searchParams.get("priority") || "balanced";
      const url = `/api/v1/router/recommend?task_type=${encodeURIComponent(taskType)}&priority=${encodeURIComponent(priority)}`;
      const { ok, status, data } = await apiFetch(url, {
        cache: "no-store",
      });
      if (!ok) {
        return NextResponse.json({ error: "获取推荐失败" }, { status });
      }
      return NextResponse.json(data);
    }

    if (action === "performance") {
      const modelName = searchParams.get("model_name");
      const url = modelName
        ? `/api/v1/router/performance?model_name=${encodeURIComponent(modelName)}`
        : "/api/v1/router/performance";
      const { ok, status, data } = await apiFetch(url, {
        cache: "no-store",
      });
      if (!ok) {
        return NextResponse.json({ error: "获取性能统计失败" }, { status });
      }
      return NextResponse.json(data);
    }

    // 默认 GET 转发
    const { ok, status, data } = await apiFetch(`/${pathname}`, {
      cache: "no-store",
    });
    if (!ok) {
      return NextResponse.json({ error: "请求失败" }, { status });
    }
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // POST /chat - 路由到最优模型
    if (request.nextUrl.pathname.endsWith("/chat")) {
      const { ok, status, data } = await apiFetch("/api/v1/router/chat", {
        method: "POST",
        body,
      });
      if (!ok) {
        return NextResponse.json({ error: "路由失败" }, { status });
      }
      return NextResponse.json(data);
    }

    // POST /cost-estimate - 估算调用成本
    if (request.nextUrl.pathname.endsWith("/cost-estimate")) {
      const { prompt, model_name = "deepseek", output_tokens = 500 } = body;
      const url = `/api/v1/router/cost-estimate?prompt=${encodeURIComponent(prompt)}&model_name=${encodeURIComponent(model_name)}&output_tokens=${output_tokens}`;
      const { ok, status, data } = await apiFetch(url, {
        method: "POST",
      });
      if (!ok) {
        return NextResponse.json({ error: "成本估算失败" }, { status });
      }
      return NextResponse.json(data);
    }

    return NextResponse.json({ error: "未知端点" }, { status: 404 });
  } catch {
    return NextResponse.json({ error: "API 服务未启动" }, { status: 503 });
  }
}
