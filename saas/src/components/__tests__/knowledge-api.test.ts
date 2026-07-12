// @vitest-environment node
import { describe, test, expect, beforeEach, afterEach, vi } from "vitest";
import { GET as listGet } from "@/app/api/knowledge/list/route";
import { GET as contentGet, POST as contentPost } from "@/app/api/knowledge/content/route";

// Mock fs module
vi.mock("fs", () => {
  const mockFiles: Record<string, string> = {
    "/mock/content/methodology/01-fan-chang-shi.md": "# 反常识方法论\n\n## 核心原则\n打破常规思维...",
    "/mock/content/templates/02-title-templates.md": "# 标题模板库\n\n## 爆款标题",
    "/mock/content/experts/writing-expert.md": "# 写作专家\n\n## 专业建议",
    "/mock/content/prompts/generate-prompt.md": "# 生成提示词\n\n## 系统提示",
  };

  return {
    readFileSync: vi.fn((path: string) => {
      const content = mockFiles[path];
      if (!content) {
        throw new Error(`ENOENT: no such file or directory, open '${path}'`);
      }
      return content;
    }),
    readdirSync: vi.fn((dirPath: string) => {
      if (dirPath.includes("content")) {
        return [
          { name: "methodology", isDirectory: () => true, isFile: () => false },
          { name: "templates", isDirectory: () => true, isFile: () => false },
          { name: "experts", isDirectory: () => true, isFile: () => false },
          { name: "prompts", isDirectory: () => true, isFile: () => false },
        ];
      }
      if (dirPath.includes("methodology")) {
        return [
          { name: "01-fan-chang-shi.md", isDirectory: () => false, isFile: () => true },
          { name: "02-ren-xing.md", isDirectory: () => false, isFile: () => true },
        ];
      }
      if (dirPath.includes("templates")) {
        return [
          { name: "02-title-templates.md", isDirectory: () => false, isFile: () => true },
        ];
      }
      if (dirPath.includes("experts")) {
        return [
          { name: "writing-expert.md", isDirectory: () => false, isFile: () => true },
        ];
      }
      if (dirPath.includes("prompts")) {
        return [
          { name: "generate-prompt.md", isDirectory: () => false, isFile: () => true },
        ];
      }
      return [];
    }),
    statSync: vi.fn((path: string) => ({
      size: 1024,
      mtime: new Date("2026-06-20T10:00:00Z"),
      isDirectory: () => false,
      isFile: () => true,
    })),
    writeFileSync: vi.fn(),
  };
});

// Mock path.join to simulate working directory
vi.mock("path", async () => {
  const actual = await vi.importActual("path");
  return {
    ...(actual as object),
    join: vi.fn((...args: string[]) => {
      // Replace process.cwd() with /mock for test
      const parts = args.map((a: string) =>
        a.includes(process.cwd()) ? a.replace(process.cwd(), "/mock") : a
      );
      return parts.join("/").replace(/\\/g, "/").replace(/\/+/g, "/");
    }),
    resolve: vi.fn((...args: string[]) => args.join("/")),
  };
});

describe("知识库 API 路由", () => {
  describe("GET /api/knowledge/list", () => {
    test("返回文件树结构，包含根目录信息", async () => {
      const res = await listGet();
      expect(res.status).toBe(200);

      const json = await res.json();
      expect(json).toHaveProperty("tree");
      expect(json).toHaveProperty("root");
      expect(Array.isArray(json.tree)).toBe(true);
    });

    test("树结构包含顶层分类文件夹", async () => {
      const res = await listGet();
      const json = await res.json();

      const topFolders = json.tree.map((n: { name: string }) => n.name);
      expect(topFolders).toContain("methodology");
      expect(topFolders).toContain("templates");
      expect(topFolders).toContain("experts");
      expect(topFolders).toContain("prompts");
    });

    test("文件夹包含正确的 type 字段", async () => {
      const res = await listGet();
      const json = await res.json();

      for (const node of json.tree) {
        expect(node.type).toBe("folder");
        expect(Array.isArray(node.children)).toBe(true);
      }
    });

    test("文件节点包含 size 和 modified 元信息", async () => {
      const res = await listGet();
      const json = await res.json();

      // Find a file leaf node
      const findFile = (nodes: unknown[]): unknown => {
        for (const n of nodes as any[]) {
          if (n.type === "file") return n;
          if (n.children) {
            const found = findFile(n.children);
            if (found) return found;
          }
        }
        return null;
      };

      const fileNode = findFile(json.tree) as any;
      expect(fileNode).not.toBeNull();
      expect(fileNode).toHaveProperty("size");
      expect(fileNode).toHaveProperty("modified");
    });
  });

  describe("GET /api/knowledge/content", () => {
    test("传入有效 path 返回文件内容和元信息", async () => {
      const req = new Request(
        "http://localhost/api/knowledge/content?path=methodology/01-fan-chang-shi.md"
      );
      const res = await contentGet(req);
      expect(res.status).toBe(200);

      const json = await res.json();
      expect(json).toHaveProperty("content");
      expect(json).toHaveProperty("path", "methodology/01-fan-chang-shi.md");
      expect(json).toHaveProperty("meta");
      expect(json.meta).toHaveProperty("wordCount");
      expect(json.meta).toHaveProperty("size");
      expect(json.meta).toHaveProperty("modified");
      expect(json.meta).toHaveProperty("tags");
      expect(json.meta).toHaveProperty("fileName");
    });

    test("缺失 path 参数时返回 400 错误", async () => {
      const req = new Request("http://localhost/api/knowledge/content");
      const res = await contentGet(req);
      expect(res.status).toBe(400);

      const json = await res.json();
      expect(json).toHaveProperty("error");
      expect(json.error).toBe("缺少 path 参数");
    });

    test("文件不存在时返回 404 错误", async () => {
      const req = new Request(
        "http://localhost/api/knowledge/content?path=nonexistent/file.md"
      );
      const res = await contentGet(req);
      expect(res.status).toBe(404);

      const json = await res.json();
      expect(json.error).toBe("文件不存在");
    });

    test("返回正确的字数统计信息", async () => {
      const req = new Request(
        "http://localhost/api/knowledge/content?path=methodology/01-fan-chang-shi.md"
      );
      const res = await contentGet(req);
      const json = await res.json();

      // mock 内容中包含中文字符
      expect(json.meta.wordCount).toBeGreaterThan(0);
    });

    test("标签从文件名中提取", async () => {
      const req = new Request(
        "http://localhost/api/knowledge/content?path=methodology/01-fan-chang-shi.md"
      );
      const res = await contentGet(req);
      const json = await res.json();

      expect(Array.isArray(json.meta.tags)).toBe(true);
      expect(json.meta.tags.length).toBeGreaterThan(0);
    });
  });

  describe("POST /api/knowledge/content", () => {
    test("有效请求返回 success", async () => {
      const req = new Request("http://localhost/api/knowledge/content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path: "methodology/01-fan-chang-shi.md",
          content: "# 更新后的内容",
        }),
      });
      const res = await contentPost(req);
      expect(res.status).toBe(200);

      const json = await res.json();
      expect(json.success).toBe(true);
    });

    test("缺失 path 参数返回 400", async () => {
      const req = new Request("http://localhost/api/knowledge/content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: "内容" }),
      });
      const res = await contentPost(req);
      expect(res.status).toBe(400);
    });

    test("缺失 content 参数返回 400", async () => {
      const req = new Request("http://localhost/api/knowledge/content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: "test.md" }),
      });
      const res = await contentPost(req);
      expect(res.status).toBe(400);
    });

    test("目录穿越攻击被拦截返回 403", async () => {
      const req = new Request("http://localhost/api/knowledge/content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          path: "../../etc/passwd",
          content: "hacked",
        }),
      });
      const res = await contentPost(req);
      expect(res.status).toBe(403);

      const json = await res.json();
      expect(json.error).toBe("无效路径");
    });
  });
});
