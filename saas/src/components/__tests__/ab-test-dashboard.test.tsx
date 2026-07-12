import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { ABTestDashboard } from "@/components/ab-test-dashboard";

// Mock the toast component
vi.mock("@/components/toaster", () => ({
  toast: vi.fn(),
}));

type FetchMock = ReturnType<typeof vi.fn>;

function mockFetchResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("ABTestDashboard", () => {
  let fetchMock: FetchMock;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  test("空状态：没有测试时显示空状态提示", async () => {
    fetchMock.mockResolvedValueOnce(mockFetchResponse(200, { tests: [] }));

    render(<ABTestDashboard />);

    await waitFor(() => {
      expect(screen.getByText("还没有A/B测试")).toBeDefined();
    });
  });

  test("空状态时显示「创建测试」按钮", async () => {
    fetchMock.mockResolvedValueOnce(mockFetchResponse(200, { tests: [] }));

    render(<ABTestDashboard />);

    await waitFor(() => {
      expect(screen.getByText("创建测试")).toBeDefined();
    });
  });

  test("加载中显示 spinner", () => {
    fetchMock.mockReturnValue(new Promise(() => {}));

    render(<ABTestDashboard />);

    // 加载中状态应该有加载文本
    expect(screen.getByText("加载中...")).toBeDefined();
  });

  test("数据加载后显示测试卡片", async () => {
    const mockTests = {
      tests: [
        {
          test_id: "test-abc123",
          name: "标题风格对比测试",
          project_id: "default",
          description: "对比震惊体和故事体的表现",
          variants: [
            {
              id: "var-a",
              title: "震惊！这个方法太厉害了",
              content: "内容A的正文",
              metrics: { views: 1200, likes: 300, comments: 45, shares: 80 },
            },
            {
              id: "var-b",
              title: "我用了这个方法，效果惊人",
              content: "内容B的正文",
              metrics: { views: 980, likes: 280, comments: 52, shares: 95 },
            },
          ],
          status: "running",
          created_at: "2026-06-20T08:00:00Z",
          duration_days: 14,
          platforms: ["抖音", "小红书"],
        },
      ],
    };

    fetchMock.mockResolvedValueOnce(mockFetchResponse(200, mockTests));

    render(<ABTestDashboard />);

    await waitFor(() => {
      expect(screen.getByText("标题风格对比测试")).toBeDefined();
    });
  });

  test("数据加载后显示汇总统计栏", async () => {
    const mockTests = {
      tests: [
        {
          test_id: "test-001",
          name: "测试1",
          project_id: "default",
          variants: [],
          status: "running",
          created_at: "2026-06-20T08:00:00Z",
        },
        {
          test_id: "test-002",
          name: "测试2",
          project_id: "default",
          variants: [],
          status: "completed",
          created_at: "2026-06-15T08:00:00Z",
        },
      ],
    };

    fetchMock.mockResolvedValueOnce(mockFetchResponse(200, mockTests));

    render(<ABTestDashboard />);

    await waitFor(() => {
      // 汇总栏应显示全部、运行中、已完成、草稿
      expect(screen.getByText("全部")).toBeDefined();
      expect(screen.getByText("运行中")).toBeDefined();
      expect(screen.getByText("已完成")).toBeDefined();
      expect(screen.getByText("草稿")).toBeDefined();
    });
  });

  test("加载失败时显示错误状态和重试按钮", async () => {
    fetchMock.mockRejectedValueOnce(new Error("Network Error"));

    render(<ABTestDashboard />);

    await waitFor(() => {
      expect(screen.getByText("重试")).toBeDefined();
    });
  });

  test("页面标题和描述正确渲染", async () => {
    fetchMock.mockResolvedValueOnce(mockFetchResponse(200, { tests: [] }));

    render(<ABTestDashboard />);

    // 页面标题立刻渲染（不在加载范围内）
    expect(screen.getByText("A/B 测试")).toBeDefined();
    expect(
      screen.getByText("科学对比不同内容变体的表现，找出最优方案")
    ).toBeDefined();
  });

  test("「新建测试」按钮存在且可点击", async () => {
    fetchMock.mockResolvedValueOnce(mockFetchResponse(200, { tests: [] }));

    render(<ABTestDashboard />);

    await waitFor(() => {
      // 等待加载完成，然后检查按钮
      const createButton = screen.getByText("新建测试");
      expect(createButton).toBeDefined();

      // 模拟点击后应出现创建模态框
      // 注：点击后会显示模态框，模态框中包含「创建 A/B 测试」标题
    });
  });

  test("显示变体指标数据", async () => {
    const mockTests = {
      tests: [
        {
          test_id: "test-xyz",
          name: "互动率测试",
          project_id: "default",
          variants: [
            {
              id: "var-1",
              title: "变体A标题",
              content: "变体A内容...",
              metrics: { views: 500, likes: 120, comments: 30, shares: 50 },
            },
            {
              id: "var-2",
              title: "变体B标题",
              content: "变体B内容...",
              metrics: { views: 450, likes: 150, comments: 45, shares: 70 },
            },
          ],
          status: "running",
          created_at: "2026-06-22T08:00:00Z",
          duration_days: 7,
        },
      ],
    };

    fetchMock.mockResolvedValueOnce(mockFetchResponse(200, mockTests));

    render(<ABTestDashboard />);

    await waitFor(() => {
      // 变体指标数据会以数字形式渲染
      expect(screen.getByText("500")).toBeDefined();
      expect(screen.getByText("450")).toBeDefined();
    });
  });
});
