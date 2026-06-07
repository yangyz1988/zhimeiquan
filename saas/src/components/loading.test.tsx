import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Loading } from "@/components/loading";

describe("Loading", () => {
  test("默认消息", () => {
    render(<Loading />);
    expect(screen.getByText("加载中...")).toBeDefined();
  });

  test("自定义消息", () => {
    render(<Loading message="数据加载中" />);
    expect(screen.getByText("数据加载中")).toBeDefined();
  });

  test("全页模式", () => {
    const { container } = render(<Loading fullPage />);
    expect(container.querySelector(".min-h-\\[400px\\]")).toBeDefined();
  });
});
