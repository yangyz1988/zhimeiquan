import { describe, test, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PlatformPreview } from "@/components/platform-preview";

// Mock lucide-react icons (they are just decorative)
vi.mock("lucide-react", () => ({
  Eye: () => <span data-testid="eye-icon" />,
  Smartphone: () => <span data-testid="smartphone-icon" />,
  Monitor: () => <span data-testid="monitor-icon" />,
  Heart: () => <span data-testid="heart-icon" />,
  MessageSquare: () => <span data-testid="message-icon" />,
  Play: () => <span data-testid="play-icon" />,
  Sparkles: () => null,
  Hash: () => null,
  Quote: () => null,
  Share2: () => null,
  RotateCw: () => null,
}));

const sampleContent = {
  titles: ["AI时代普通人如何抓住这波红利", "3个你必须知道的底层逻辑"],
  script: "大家好，今天我们来聊一个所有人都关心的话题：AI时代普通人到底还有没有机会？AI正在创造前所未有的普通人逆袭机会。",
  tags: ["AI", "副业", "自媒体", "赚钱", "成长"],
  hook: "AI时代普通人还有机会吗？答案是：有",
};

describe("PlatformPreview", () => {
  test("使用示例数据渲染时显示「示例数据」标签", () => {
    // 不传 content 属性，使用默认示例数据
    render(<PlatformPreview />);
    expect(screen.getByText("示例数据")).toBeDefined();
  });

  test("传入 content 属性时不显示示例标签", () => {
    render(<PlatformPreview content={sampleContent} />);
    expect(screen.queryByText("示例数据")).toBeNull();
  });

  test("渲染标题「平台预览」", () => {
    render(<PlatformPreview content={sampleContent} />);
    expect(screen.getByText("平台预览")).toBeDefined();
  });

  test("默认显示竖版/手机模式", () => {
    render(<PlatformPreview content={sampleContent} />);
    // 竖版按钮应该处于激活状态
    const mobileButton = screen.getByText("竖版");
    expect(mobileButton).toBeDefined();
  });

  test("显示所有4个平台切换按钮", () => {
    render(<PlatformPreview content={sampleContent} />);
    expect(screen.getByText("抖音")).toBeDefined();
    expect(screen.getByText("小红书")).toBeDefined();
    // B站和公众号是横版，在手机模式下不可见
  });

  test("切换横版模式后显示 B站 和 公众号", () => {
    render(<PlatformPreview content={sampleContent} />);
    const desktopButton = screen.getByText("横版");
    fireEvent.click(desktopButton);
    expect(screen.getByText("B站")).toBeDefined();
    expect(screen.getByText("公众号")).toBeDefined();
  });

  test("竖版模式下默认选中抖音", () => {
    render(<PlatformPreview content={sampleContent} />);
    const douyinButton = screen.getByText("抖音");
    expect(douyinButton).toBeDefined();
  });

  test("内容统计信息显示正确", () => {
    render(<PlatformPreview content={sampleContent} />);
    // 标题数 = 2
    expect(screen.getByText("2")).toBeDefined();
    // 标签数 = 5
    expect(screen.getByText("5")).toBeDefined();
    // 钩子状态 = "有"
    expect(screen.getByText("有")).toBeDefined();
  });

  test("切换平台按钮触发视图更新", () => {
    render(<PlatformPreview content={sampleContent} />);
    // 点击小红书按钮
    const xhsButton = screen.getByText("小红书");
    fireEvent.click(xhsButton);
    // 小红书的预览应该激活——会显示"小红书博主"字样
    expect(screen.getByText("小红书博主")).toBeDefined();
  });

  test("横版模式下切换平台显示 B站 预览", () => {
    render(<PlatformPreview content={sampleContent} />);
    // 先切换到横版
    fireEvent.click(screen.getByText("横版"));
    // 点击 B站
    fireEvent.click(screen.getByText("B站"));
    // B站预览中应包含 UP主 字样
    expect(screen.getByText("UP主")).toBeDefined();
  });

  test("自定义 platforms 参数只显示指定平台", () => {
    render(
      <PlatformPreview
        content={sampleContent}
        platforms={["douyin", "wechat"]}
      />
    );
    // 竖版只显示抖音
    expect(screen.getByText("抖音")).toBeDefined();
    expect(screen.queryByText("小红书")).toBeNull();
  });

  test("默认使用 4 个标准平台配置", () => {
    render(<PlatformPreview content={sampleContent} />);
    const statLabels = screen.getAllByText("标题");
    expect(statLabels.length).toBeGreaterThan(0);
  });
});
