import { NextRequest, NextResponse } from "next/server";
import { readFileSync, readdirSync, statSync } from "fs";
import { join, relative, extname } from "path";

const CONTENT_DIR = join(process.cwd(), "..", "..", "content");

interface TreeNode {
  id: string;
  name: string;
  path: string;
  type: "folder" | "file";
  children?: TreeNode[];
  size?: number;
  modified?: string;
}

function buildTree(dirPath: string, basePath: string = ""): TreeNode[] {
  const entries: TreeNode[] = [];

  try {
    const items = readdirSync(dirPath, { withFileTypes: true });
    for (const item of items.sort((a, b) => {
      // Folders first, then alphabetical
      if (a.isDirectory() && !b.isDirectory()) return -1;
      if (!a.isDirectory() && b.isDirectory()) return 1;
      return a.name.localeCompare(b.name);
    })) {
      const fullPath = join(dirPath, item.name);
      const relPath = basePath ? `${basePath}/${item.name}` : item.name;

      if (item.isDirectory()) {
        const children = buildTree(fullPath, relPath);
        entries.push({
          id: relPath,
          name: item.name,
          path: relPath,
          type: "folder",
          children,
        });
      } else if (item.name.endsWith(".md")) {
        const stats = statSync(fullPath);
        entries.push({
          id: relPath,
          name: item.name,
          path: relPath,
          type: "file",
          size: stats.size,
          modified: stats.mtime.toISOString(),
        });
      }
    }
  } catch {
    // Directory doesn't exist
  }

  return entries;
}

export async function GET() {
  try {
    const tree = buildTree(CONTENT_DIR);
    return NextResponse.json({ tree, root: CONTENT_DIR });
  } catch (error) {
    console.error("Knowledge list error:", error);
    return NextResponse.json({ error: "无法读取知识库目录" }, { status: 500 });
  }
}
