import { describe, test, expect, vi, beforeEach } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { CopyButton } from "@/components/copy-button";

describe("CopyButton", () => {
  beforeEach(() => {
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  test("渲染默认状态", () => {
    render(<CopyButton text="hello" />);
    expect(screen.getByText("复制")).toBeDefined();
  });

  test("点击后调用 clipboard.writeText", async () => {
    render(<CopyButton text="hello world" />);
    const button = screen.getByText("复制");
    fireEvent.click(button);
    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith("hello world");
    });
  });

  test("复制后显示已复制", async () => {
    render(<CopyButton text="hello" />);
    fireEvent.click(screen.getByText("复制"));
    await waitFor(() => {
      expect(screen.getByText("已复制")).toBeDefined();
    });
  });

  test("自定义 label", () => {
    render(<CopyButton text="x" label="Copy" />);
    expect(screen.getByText("Copy")).toBeDefined();
  });
});
