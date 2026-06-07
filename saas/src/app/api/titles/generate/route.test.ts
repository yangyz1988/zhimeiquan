// @vitest-environment node
import { describe, test, expect, beforeEach, afterEach, vi } from "vitest";
import { POST } from "./route";

type FetchMock = ReturnType<typeof vi.fn>;

function buildRequest(body: unknown): Request {
  return new Request("http://localhost/api/titles/generate", {
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

describe("POST /api/titles/generate", () => {
  let fetchMock: FetchMock;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  test("成功：返回 5 个标题", async () => {
    const titles = [
      "震惊！这个习惯改变了我",
      "90% 的人都不知道的秘密",
      "3 步教你搞定一切",
      "为什么聪明人都在用这个",
      "别再浪费时间了",
    ];
    fetchMock.mockResolvedValueOnce(mockFetchResponse(200, { titles }));

    const res = await POST(
      buildRequest({
        topic: "AI 自媒体",
        platform: "xiaohongshu",
        count: 5,
      }) as never
    );

    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.titles).toHaveLength(5);
    expect(Array.isArray(json.titles)).toBe(true);
  });

  test("count=3：返回 3 个标题", async () => {
    const titles = ["标题 A", "标题 B", "标题 C"];
    fetchMock.mockResolvedValueOnce(mockFetchResponse(200, { titles }));

    const res = await POST(
      buildRequest({
        topic: "副业赚钱",
        platform: "douyin",
        count: 3,
      }) as never
    );

    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.titles).toHaveLength(3);
  });

  test("count=1：返回 1 个标题", async () => {
    const titles = ["唯一标题"];
    fetchMock.mockResolvedValueOnce(mockFetchResponse(200, { titles }));

    const res = await POST(
      buildRequest({
        topic: "测试主题",
        platform: "wechat",
        count: 1,
      }) as never
    );

    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.titles).toHaveLength(1);
    expect(json.titles[0]).toBe("唯一标题");
  });

  test("上游失败：返回 500（转发上游状态码）", async () => {
    fetchMock.mockResolvedValueOnce(
      mockFetchResponse(500, { error: "upstream error" })
    );

    const res = await POST(
      buildRequest({ topic: "x", platform: "douyin", count: 5 }) as never
    );

    expect(res.status).toBe(500);
    const json = await res.json();
    expect(json.error).toBe("生成失败");
  });

  test("网络异常：fetch 抛错时返回 503", async () => {
    fetchMock.mockRejectedValueOnce(new Error("ECONNREFUSED"));

    const res = await POST(
      buildRequest({ topic: "x", platform: "douyin", count: 5 }) as never
    );

    expect(res.status).toBe(503);
    const json = await res.json();
    expect(json.error).toBe("API 服务未启动");
  });
});
