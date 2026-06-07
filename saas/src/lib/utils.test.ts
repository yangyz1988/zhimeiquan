import { describe, test, expect } from "vitest";
import { cn } from "./utils";

describe("cn()", () => {
  test("合并多个字符串类名", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  test("过滤 falsy 值：undefined / null / false / 空字符串", () => {
    expect(cn("foo", undefined, null, false, "", "bar")).toBe("foo bar");
  });

  test("处理数组形式的输入", () => {
    expect(cn(["foo", "bar"], "baz")).toBe("foo bar baz");
  });

  test("处理嵌套数组和对象", () => {
    expect(cn("foo", ["bar", ["baz", { qux: true, skip: false }]])).toBe(
      "foo bar baz qux"
    );
  });

  test("tailwind-merge 去重：相同属性后值覆盖前值", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
    expect(cn("text-red-500", "text-blue-500")).toBe("text-blue-500");
  });

  test("tailwind-merge 不冲突的类全部保留", () => {
    expect(cn("px-2", "py-4", "text-sm")).toBe("px-2 py-4 text-sm");
  });

  test("条件类：对象形式 { active: isActive }", () => {
    const isActive = true;
    const isDisabled = false;
    expect(cn("base", { active: isActive, disabled: isDisabled })).toBe(
      "base active"
    );
  });

  test("无参数返回空字符串", () => {
    expect(cn()).toBe("");
  });

  test("只传 falsy 值返回空字符串", () => {
    expect(cn(undefined, null, false, "")).toBe("");
  });

  test("混合：字符串 + 数组 + 条件对象 + tailwind 合并", () => {
    const result = cn(
      "px-2 py-1",
      ["rounded", "shadow"],
      { "font-bold": true, hidden: false },
      "px-4"
    );
    expect(result).toBe("py-1 rounded shadow font-bold px-4");
  });
});
