// @vitest-environment node
import { describe, test, expect, beforeEach, afterEach, vi } from "vitest";
import { POST } from "./route";

type FetchMock = ReturnType<typeof vi.fn>;

function buildRequest(body: unknown): Request {
  return new Request("http://localhost/api/content/score", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function mockFetchResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("POST /api/content/score", () => {
  let fetchMock: FetchMock;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  test("成功：返回 200 + Fire Score 五维结构", async () => {
    const fireScore = {
      total: 88,
      level: "S",
      dimensions: {
        hook: 18,
        emotion: 17,
        value: 18,
        shareability: 17,
        readability: 18,
      },
      suggestions: ["开头加钩子", "提升情绪张力"],
    };
    fetchMock.mockResolvedValueOnce(mockFetchResponse(200, fireScore));

    const res = await POST(
      buildRequest({
        title: "震惊！这个习惯改变了我",
        body: "正文内容...",
        platform: "xiaohongshu",
      }) as never
    );

    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json).toEqual(fireScore);
    expect(json.dimensions).toHaveProperty("hook");
    expect(json.dimensions).toHaveProperty("emotion");
    expect(json.dimensions).toHaveProperty("value");
    expect(json.dimensions).toHaveProperty("shareability");
    expect(json.dimensions).toHaveProperty("readability");
  });

  test("缺参数 title：返回 400（上游校验失败）", async () => {
    fetchMock.mockResolvedValueOnce(
      mockFetchResponse(400, { error: "title is required" })
    );

    const res = await POST(
      buildRequest({ body: "正文", platform: "douyin" }) as never
    );

    expect(res.status).toBe(400);
    const json = await res.json();
    expect(json).toHaveProperty("error");
  });

  test("缺参数 body：返回 400（上游校验失败）", async () => {
    fetchMock.mockResolvedValueOnce(
      mockFetchResponse(400, { error: "body is required" })
    );

    const res = await POST(
      buildRequest({
        title: "标题",
        platform: "wechat",
      }) as never
    );

    expect(res.status).toBe(400);
  });

  test("缺参数 platform：返回 400（上游校验失败）", async () => {
    fetchMock.mockResolvedValueOnce(
      mockFetchResponse(400, { error: "platform is required" })
    );

    const res = await POST(
      buildRequest({ title: "标题", body: "正文" }) as never
    );

    expect(res.status).toBe(400);
  });

  test("DeepSeek API 失败：fetch 抛错时返回 503", async () => {
    fetchMock.mockRejectedValueOnce(new Error("network down"));

    const res = await POST(
      buildRequest({
        title: "标题",
        body: "正文",
        platform: "douyin",
      }) as never
    );

    expect(res.status).toBe(503);
    const json = await res.json();
    expect(json.error).toBe("API 服务未启动");
  });

  test("DeepSeek 上游 500：转发 500", async () => {
    fetchMock.mockResolvedValueOnce(
      mockFetchResponse(500, { error: "internal" })
    );

    const res = await POST(
      buildRequest({
        title: "标题",
        body: "正文",
        platform: "douyin",
      }) as never
    );

    expect(res.status).toBe(500);
  });
});
