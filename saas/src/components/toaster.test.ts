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
  });
});
