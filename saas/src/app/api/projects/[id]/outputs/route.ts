import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const authResult = await requireAuth();
  if ("status" in authResult) return authResult;
  const { userId } = authResult;

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
      tags: body.tags ?? undefined,
      fireScore: body.fireScore ?? null,
      level: body.level,
    },
  });

  return NextResponse.json(output);
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const authResult = await requireAuth();
  if ("status" in authResult) return authResult;
  const { userId } = authResult;

  const { id } = await params;

  const project = await prisma.project.findFirst({
    where: { id, userId },
  });
  if (!project) {
    return NextResponse.json({ error: "项目不存在" }, { status: 404 });
  }

  const outputs = await prisma.contentOutput.findMany({
    where: { projectId: id },
    orderBy: { createdAt: "desc" },
  });

  return NextResponse.json(outputs);
}
