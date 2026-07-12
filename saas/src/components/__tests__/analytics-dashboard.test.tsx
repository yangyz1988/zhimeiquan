import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { AnalyticsDashboard } from "@/components/analytics-dashboard";

// Mock the fetch API
type FetchMock = ReturnType<typeof vi.fn>;

function mockFetchResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const mockAnalyticsData = {
  total_content: 42,
  total_views: 125000,
  total_likes: 8900,
  total_comments: 1200,
  total_shares: 3400,
  avg_engagement: 4.2,
  content_list: [
    {
      title: "AI时代普通人如何抓住红利",
      platform: "抖音",
      metrics: { views: 35000, likes: 2800, comments: 450, shares: 1200 },
      fire_score: 88,
      published_at: "2026-06-20T10:00:00Z",
    },
    {
      title: "3个你必须知道的底层逻辑",
      platform: "小红书",
      metrics: { views: 22000, likes: 1900, comments: 320, shares: 800 },
      fire_score: 82,
      published_at: "2026-06-21T14:00:00Z",
    },
    {
      title: "90%的人都不知道的秘密",
      platform: "B站",
      metrics: { views: 18000, likes: 1500, comments: 280, shares: 600 },
      fire_score: 76,
      published_at: "2026-06-22T08:00:00Z",
    },
  ],
};

const mockPlatformsData = {
  platforms: {
    "抖音": { count: 15, views: 52000, likes: 3800 },
    "小红书": { count: 12, views: 35000, likes: 2600 },
    "B站": { count: 10, views: 28000, likes: 1800 },
    "公众号": { count: 5, views: 10000, likes: 700 },
  },
};

describe("AnalyticsDashboard", () => {
  let fetchMock: FetchMock;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  test("初始加载状态：显示骨架屏和加载指示", () => {
    // Never resolve fetch to keep loading state
    fetchMock.mockReturnValue(new Promise(() => {}));

    render(<AnalyticsDashboard />);

    // 验证骨架屏元素存在（animate-pulse 类表明正在加载）
    const skeletonElements = document.querySelectorAll(".animate-pulse");
    expect(skeletonElements.length).toBeGreaterThan(0);
  });

  test("数据加载后显示统计卡片", async () => {
    fetchMock
      .mockResolvedValueOnce(mockFetchResponse(200, mockAnalyticsData))
      .mockResolvedValueOnce(mockFetchResponse(200, mockPlatformsData));

    render(<AnalyticsDashboard />);

    // 等待数据加载完成
    await waitFor(() => {
      expect(screen.getByText("数据仪表盘")).toBeDefined();
    });

    // 验证统计卡片
    expect(screen.getByText("总内容数")).toBeDefined();
    expect(screen.getByText("总曝光")).toBeDefined();
    expect(screen.getByText("总点赞")).toBeDefined();
    expect(screen.getByText("总评论")).toBeDefined();
    expect(screen.getByText("总分享")).toBeDefined();
    expect(screen.getByText("平均互动率")).toBeDefined();

    // 验证数值显示（125000 应格式化为 12.5w）
    expect(screen.getByText("12.5w")).toBeDefined();
  });

  test("数据加载后显示内容排行表格", async () => {
    fetchMock
      .mockResolvedValueOnce(mockFetchResponse(200, mockAnalyticsData))
      .mockResolvedValueOnce(mockFetchResponse(200, mockPlatformsData));

    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText("内容排行")).toBeDefined();
    });

    // 验证表格头部
    expect(screen.getByText("标题")).toBeDefined();
    expect(screen.getByText("平台")).toBeDefined();
    expect(screen.getByText("Fire Score")).toBeDefined();

    // 验证内容列表中的标题出现
    expect(screen.getByText("AI时代普通人如何抓住红利")).toBeDefined();
    expect(screen.getByText("3个你必须知道的底层逻辑")).toBeDefined();
  });

  test("数据加载后显示 Fire Score 趋势和平台分布", async () => {
    fetchMock
      .mockResolvedValueOnce(mockFetchResponse(200, mockAnalyticsData))
      .mockResolvedValueOnce(mockFetchResponse(200, mockPlatformsData));

    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Fire Score 趋势")).toBeDefined();
      expect(screen.getByText("平台分布")).toBeDefined();
    });

    // 验证平台分布图例
    expect(screen.getByText("抖音")).toBeDefined();
    expect(screen.getByText("小红书")).toBeDefined();
    expect(screen.getByText("B站")).toBeDefined();
    expect(screen.getByText("公众号")).toBeDefined();
  });

  test("API 返回空数据时显示无数据状态", async () => {
    fetchMock
      .mockResolvedValueOnce(mockFetchResponse(200, { total_content: 0, total_views: 0, total_likes: 0, total_comments: 0, total_shares: 0, avg_engagement: 0, content_list: [] }))
      .mockResolvedValueOnce(mockFetchResponse(200, { platforms: {} }));

    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText("暂无数据")).toBeDefined();
    });
  });

  test("API 请求失败时显示无数据状态", async () => {
    fetchMock
      .mockRejectedValueOnce(new Error("Network Error"))
      .mockRejectedValueOnce(new Error("Network Error"));

    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText("暂无数据")).toBeDefined();
    });
  });

  test("时间周期切换按钮存在", async () => {
    fetchMock
      .mockResolvedValueOnce(mockFetchResponse(200, mockAnalyticsData))
      .mockResolvedValueOnce(mockFetchResponse(200, mockPlatformsData));

    render(<AnalyticsDashboard />);

    await waitFor(() => {
      expect(screen.getByText("7天")).toBeDefined();
      expect(screen.getByText("30天")).toBeDefined();
      expect(screen.getByText("90天")).toBeDefined();
    });
  });
});
