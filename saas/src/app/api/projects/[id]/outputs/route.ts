import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { prisma } from "@/lib/prisma";
import { Prisma } from "@prisma/client";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "未登录" }, { status: 401 });
  }

  const { id } = await params;
  const body = await request.json();

  const project = await prisma.project.findFirst({
    where: { id, userId },
  });

  if (!project) {
    return NextResponse.json({ error: "项目不存在" }, { status: 404 });
  }

  const output = await prisma.contentOutput.create({
    data: {
      projectId: id,
      title: body.title,
      body: body.body,
      script: body.script,
      tags: body.tags ? JSON.stringify(body.tags) : null,
      fireScore: body.fireScore ?? Prisma.JsonNull,
      level: body.level,
    },
  });

  return NextResponse.json(output);
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "未登录" }, { status: 401 });
  }

  const { id } = await params;
  const outputs = await prisma.contentOutput.findMany({
    where: { projectId: id },
    orderBy: { createdAt: "desc" },
  });

  return NextResponse.json(outputs);
}
