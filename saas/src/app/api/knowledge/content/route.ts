import { NextRequest, NextResponse } from "next/server";
import { readFileSync, writeFileSync, statSync } from "fs";
import { join } from "path";

const CONTENT_DIR = join(process.cwd(), "..", "..", "content");

export async function GET(request: NextRequest) {
  const pathParam = request.nextUrl.searchParams.get("path");

  if (!pathParam) {
    return NextResponse.json({ error: "缺少 path 参数" }, { status: 400 });
  }

  // Security: prevent directory traversal
  const safePath = pathParam.replace(/\.\.\//g, "").replace(/\.\.\\/g, "");
  const fullPath = join(CONTENT_DIR, safePath);

  // Verify the resolved path is within CONTENT_DIR
  if (!fullPath.startsWith(CONTENT_DIR)) {
    return NextResponse.json({ error: "无效路径" }, { status: 403 });
  }

  try {
    const content = readFileSync(fullPath, "utf-8");
    const stats = statSync(fullPath);

    // Extract simple word count (Chinese + English)
    const chineseChars = (content.match(/[一-鿿]/g) || []).length;
    const englishWords = (content.match(/[a-zA-Z]+/g) || []).length;
    const wordCount = chineseChars + englishWords;

    // Extract tags from filename
    const fileName = safePath.split("/").pop() || "";
    const tags = fileName
      .replace(/\.md$/, "")
      .split(/[-_]/)
      .filter(Boolean);

    return NextResponse.json({
      path: safePath,
      content,
      meta: {
        size: stats.size,
        modified: stats.mtime.toISOString(),
        wordCount,
        tags,
        fileName,
      },
    });
  } catch {
    return NextResponse.json({ error: "文件不存在" }, { status: 404 });
  }
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { path: pathParam, content } = body;

  if (!pathParam || content === undefined) {
    return NextResponse.json({ error: "缺少 path 或 content 参数" }, { status: 400 });
  }

  // Security: prevent directory traversal
  const safePath = pathParam.replace(/\.\.\//g, "").replace(/\.\.\\/g, "");
  const fullPath = join(CONTENT_DIR, safePath);

  if (!fullPath.startsWith(CONTENT_DIR)) {
    return NextResponse.json({ error: "无效路径" }, { status: 403 });
  }

  try {
    writeFileSync(fullPath, content, "utf-8");
    return NextResponse.json({ success: true, path: safePath });
  } catch (error) {
    console.error("Knowledge save error:", error);
    return NextResponse.json({ error: "保存失败" }, { status: 500 });
  }
}
