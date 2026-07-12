// @vitest-environment node
import { describe, test, expect, beforeEach, afterEach, vi } from "vitest";
import { POST } from "@/app/api/stream/generate/route";

// Mock requireAuth to return success
vi.mock("@/lib/auth", () => ({
  requireAuth: vi.fn().mockResolvedValue(undefined),
}));

type FetchMock = ReturnType<typeof vi.fn>;

function buildRequest(body: unknown): Request {
  return new Request("http://localhost/api/stream/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function buildSSEResponse(): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(encoder.encode("data: {\"content\":\"正在生成...\"}\n\n"));
      controller.enqueue(encoder.encode("data: {\"content\":\"AI时代普通人如何\"}\n\n"));
      controller.enqueue(encoder.encode("data: [DONE]\n\n"));
      controller.close();
    },
  });

  return new Response(stream, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
    },
  });
}

describe("POST /api/stream/generate", () => {
  let fetchMock: FetchMock;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  test("成功请求返回 SSE 流式响应", async () => {
    fetchMock.mockResolvedValueOnce(buildSSEResponse());

    const res = await POST(
      buildRequest({
        topic: "AI 自媒体",
        platform: "xiaohongshu",
        style: "故事体",
      }) as never
    );

    expect(res.status).toBe(200);
    expect(res.headers.get("Content-Type")).toBe("text/event-stream");
    expect(res.headers.get("Cache-Control")).toBe("no-cache");
  });

  test("透传 SSE 响应头：Connection 和 X-Accel-Buffering", async () => {
    fetchMock.mockResolvedValueOnce(buildSSEResponse());

    const res = await POST(
      buildRequest({
        topic: "AI 工具推荐",
        platform: "douyin",
      }) as never
    );

    expect(res.headers.get("Connection")).toBe("keep-alive");
    expect(res.headers.get("X-Accel-Buffering")).toBe("no");
  });

  test("后端返回非 200 时转发错误状态码", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ error: "流式生成失败" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      })
    );

    const res = await POST(
      buildRequest({
        topic: "测试",
        platform: "wechat",
      }) as never
    );

    expect(res.status).toBe(400);

    const json = await res.json();
    expect(json.error).toBe("流式生成失败");
  });

  test("后端返回 500 时转发 500 错误", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ error: "流式生成失败" }), {
        status: 500,
        headers: { "Content-Type": "application/json" },
      })
    );

    const res = await POST(
      buildRequest({
        topic: "测试",
        platform: "bilibili",
      }) as never
    );

    expect(res.status).toBe(500);

    const json = await res.json();
    expect(json.error).toBe("流式生成失败");
  });

  test("网络异常时返回 503 服务不可用", async () => {
    fetchMock.mockRejectedValueOnce(new Error("ECONNREFUSED"));

    const res = await POST(
      buildRequest({
        topic: "测试",
        platform: "douyin",
      }) as never
    );

    expect(res.status).toBe(503);

    const json = await res.json();
    expect(json.error).toBe("API 服务未启动");
  });

  test("SSE 响应体是可读流", async () => {
    fetchMock.mockResolvedValueOnce(buildSSEResponse());

    const res = await POST(
      buildRequest({
        topic: "AI 写作",
        platform: "xiaohongshu",
      }) as never
    );

    expect(res.body).not.toBeNull();

    // 验证 body 是 ReadableStream
    const reader = res.body!.getReader();
    expect(reader).toBeDefined();

    // 读取第一个 chunk 验证内容
    const { done, value } = await reader.read();
    expect(done).toBe(false);
    const text = new TextDecoder().decode(value);
    expect(text).toContain("data:");
  });
});
