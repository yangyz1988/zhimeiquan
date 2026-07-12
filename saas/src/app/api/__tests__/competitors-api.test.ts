// @vitest-environment node
import { describe, test, expect, beforeEach, afterEach, vi } from "vitest";
import { GET, POST } from "@/app/api/competitors/route";
import { GET as IdGET, DELETE } from "@/app/api/competitors/[id]/route";

// Mock apiFetch
vi.mock("@/lib/api", () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from "@/lib/api";
const mockApiFetch = apiFetch as ReturnType<typeof vi.fn>;

describe("竞品 API 路由", () => {
  describe("GET /api/competitors", () => {
    test("未传 user_id 返回空数组", async () => {
      const req = new Request("http://localhost/api/competitors");
      const res = await GET(req);
      expect(res.status).toBe(200);

      const json = await res.json();
      expect(json.competitors).toEqual([]);
    });

    test("有 user_id 时调用后端 API 并返回数据", async () => {
      const mockData = {
        competitors: [
          { id: "1", name: "竞品A", platform: "抖音", followers: 100000 },
          { id: "2", name: "竞品B", platform: "小红书", followers: 50000 },
        ],
      };

      mockApiFetch.mockResolvedValueOnce({ ok: true, status: 200, data: mockData });

      const req = new Request("http://localhost/api/competitors?user_id=user123");
      const res = await GET(req);
      expect(res.status).toBe(200);

      const json = await res.json();
      expect(json.competitors).toHaveLength(2);
      expect(json.competitors[0].name).toBe("竞品A");
      expect(json.competitors[1].name).toBe("竞品B");
    });

    test("后端返回失败时返回空数组", async () => {
      mockApiFetch.mockResolvedValueOnce({ ok: false, status: 500, data: {} });

      const req = new Request("http://localhost/api/competitors?user_id=user123");
      const res = await GET(req);
      expect(res.status).toBe(200);

      const json = await res.json();
      expect(json.competitors).toEqual([]);
    });

    test("API 异常时返回空数组", async () => {
      mockApiFetch.mockRejectedValueOnce(new Error("Network error"));

      const req = new Request("http://localhost/api/competitors?user_id=user123");
      const res = await GET(req);
      expect(res.status).toBe(200);

      const json = await res.json();
      expect(json.competitors).toEqual([]);
    });
  });

  describe("POST /api/competitors", () => {
    test("有效请求创建竞品条目并返回数据", async () => {
      const newCompetitor = {
        name: "新竞品",
        platform: "B站",
        url: "https://bilibili.com/competitor",
      };

      const mockResponse = {
        id: "new-id-123",
        ...newCompetitor,
        created_at: "2026-06-25T10:00:00Z",
      };

      mockApiFetch.mockResolvedValueOnce({ ok: true, status: 200, data: mockResponse });

      const req = new Request("http://localhost/api/competitors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newCompetitor),
      });

      const res = await POST(req);
      expect(res.status).toBe(200);

      const json = await res.json();
      expect(json.id).toBe("new-id-123");
      expect(json.name).toBe("新竞品");
      expect(json.platform).toBe("B站");
    });

    test("后端拒绝时转发错误", async () => {
      mockApiFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        data: { error: "缺少必填字段" },
      });

      const req = new Request("http://localhost/api/competitors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "不完整数据" }),
      });

      const res = await POST(req);
      expect(res.status).toBe(400);

      const json = await res.json();
      expect(json.error).toBe("缺少必填字段");
    });

    test("网络异常时返回 503", async () => {
      mockApiFetch.mockRejectedValueOnce(new Error("ECONNREFUSED"));

      const req = new Request("http://localhost/api/competitors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "测试竞品", platform: "抖音" }),
      });

      const res = await POST(req);
      expect(res.status).toBe(503);

      const json = await res.json();
      expect(json.error).toBe("API 服务未启动");
    });
  });

  describe("GET /api/competitors/[id]", () => {
    test("获取竞品分析数据", async () => {
      const mockAnalysis = {
        id: "comp-1",
        name: "竞品A",
        analysis: {
          strengths: ["内容质量高", "更新频率稳定"],
          weaknesses: ["互动率偏低"],
        },
      };

      mockApiFetch.mockResolvedValueOnce({ ok: true, status: 200, data: mockAnalysis });

      const req = new Request("http://localhost/api/competitors/comp-1");
      const res = await IdGET(req, { params: Promise.resolve({ id: "comp-1" }) });
      expect(res.status).toBe(200);

      const json = await res.json();
      expect(json.name).toBe("竞品A");
      expect(json.analysis.strengths).toContain("内容质量高");
    });

    test("后端返回 404 时转发", async () => {
      mockApiFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        data: { error: "分析数据不存在" },
      });

      const req = new Request("http://localhost/api/competitors/comp-nonexist");
      const res = await IdGET(req, { params: Promise.resolve({ id: "comp-nonexist" }) });
      expect(res.status).toBe(404);

      const json = await res.json();
      expect(json.error).toBe("分析数据不存在");
    });
  });

  describe("DELETE /api/competitors/[id]", () => {
    test("成功删除返回确认", async () => {
      mockApiFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        data: { success: true, message: "已删除" },
      });

      const req = new Request("http://localhost/api/competitors/comp-1", {
        method: "DELETE",
      });
      const res = await DELETE(req, { params: Promise.resolve({ id: "comp-1" }) });
      expect(res.status).toBe(200);

      const json = await res.json();
      expect(json.success).toBe(true);
    });

    test("删除不存在条目返回错误", async () => {
      mockApiFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        data: { error: "竞品不存在" },
      });

      const req = new Request("http://localhost/api/competitors/comp-nonexist", {
        method: "DELETE",
      });
      const res = await DELETE(req, { params: Promise.resolve({ id: "comp-nonexist" }) });
      expect(res.status).toBe(404);

      const json = await res.json();
      expect(json.error).toBe("竞品不存在");
    });

    test("删除时网络异常返回 503", async () => {
      mockApiFetch.mockRejectedValueOnce(new Error("ECONNREFUSED"));

      const req = new Request("http://localhost/api/competitors/comp-1", {
        method: "DELETE",
      });
      const res = await DELETE(req, { params: Promise.resolve({ id: "comp-1" }) });
      expect(res.status).toBe(503);

      const json = await res.json();
      expect(json.error).toBe("API 服务未启动");
    });
  });
});
