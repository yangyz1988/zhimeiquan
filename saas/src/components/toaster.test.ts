import { describe, test, expect, vi } from "vitest";
import { toast } from "@/components/toaster";

describe("toast()", () => {
  test("不应该抛出", () => {
    expect(() => toast("测试消息")).not.toThrow();
  });

  test("接受不同类型", () => {
    expect(() => toast("成功", "success")).not.toThrow();
    expect(() => toast("错误", "error")).not.toThrow();
    expect(() => toast("信息", "info")).not.toThrow();
    expect(() => toast("警告", "warning")).not.toThrow();
  });

  test("接受操作按钮", () => {
    const action = { label: "撤销", onClick: vi.fn() };
    expect(() => toast("已删除", "warning", action)).not.toThrow();
  });

  test("接受自定义时长", () => {
    expect(() => toast("持久消息", "info", undefined, 10000)).not.toThrow();
  });

  test("便捷方法正常工作", () => {
    expect(() => toast.success("成功")).not.toThrow();
    expect(() => toast.error("错误")).not.toThrow();
    expect(() => toast.warning("警告")).not.toThrow();
    expect(() => toast.info("信息")).not.toThrow();
  });
});
