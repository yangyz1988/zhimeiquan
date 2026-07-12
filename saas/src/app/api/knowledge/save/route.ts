import { NextRequest, NextResponse } from "next/server";
import { writeFileSync, mkdirSync, existsSync } from "fs";
import { join, normalize, relative } from "path";

const CONTENT_DIR = join(process.cwd(), "..", "..", "content");

/**
 * 验证路径是否安全（防止目录遍历攻击）
 * 确保解析后的路径在 CONTENT_DIR 范围内
 */
function isValidPath(requestedPath: string): { safe: boolean; fullPath: string; error?: string } {
  // 移除所有路径遍历尝试（.. 和 .）
  const normalized = normalize(requestedPath).replace(/\\/g, "/");

  // 拒绝包含 parent reference 的路径
  if (normalized.includes("..")) {
    return { safe: false, fullPath: "", error: "路径不能包含父目录引用" };
  }

  // 拒绝绝对路径
  if (normalized.startsWith("/")) {
    return { safe: false, fullPath: "", error: "路径不能以 / 开头" };
  }

  // 只允许 .md 文件
  if (!normalized.endsWith(".md")) {
    return { safe: false, fullPath: "", error: "仅支持 .md 文件" };
  }

  const fullPath = join(CONTENT_DIR, normalized);

  // 关键安全检查：确保最终路径在 CONTENT_DIR 内
  const relativePath = relative(CONTENT_DIR, fullPath);
  if (relativePath.startsWith("..") || relativePath === "") {
    return { safe: false, fullPath: "", error: "无效路径" };
  }

  return { safe: true, fullPath };
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { path: filePath, content } = body;

    // 参数验证
    if (!filePath || typeof filePath !== "string") {
      return NextResponse.json(
        { error: "缺少 path 参数", code: "ERR_MISSING_PATH" },
        { status: 400 }
      );
    }
    if (content === undefined || typeof content !== "string") {
      return NextResponse.json(
        { error: "缺少 content 参数", code: "ERR_MISSING_CONTENT" },
        { status: 400 }
      );
    }

    // 安全检查
    const { safe, fullPath, error } = isValidPath(filePath);
    if (!safe) {
      return NextResponse.json(
        { error: error || "无效路径", code: "ERR_INVALID_PATH" },
        { status: 403 }
      );
    }

    // 确保目标目录存在
    const dirPath = fullPath.substring(0, fullPath.lastIndexOf("/"));
    if (!existsSync(dirPath)) {
      mkdirSync(dirPath, { recursive: true });
    }

    // 写入文件
    writeFileSync(fullPath, content, "utf-8");

    return NextResponse.json({
      success: true,
      path: filePath,
      message: "保存成功",
    });
  } catch (error) {
    console.error("Knowledge save error:", error);
    return NextResponse.json(
      { error: "保存失败，请检查文件权限和磁盘空间", code: "ERR_SAVE_FAILED" },
      { status: 500 }
    );
  }
}
