import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

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
    include: { outputs: true },
  });

  if (!project) {
    return NextResponse.json({ error: "项目不存在" }, { status: 404 });
  }

  return NextResponse.json(project);
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const authResult = await requireAuth();
  if ("status" in authResult) return authResult;
  const { userId } = authResult;

  const { id } = await params;
  const body = await request.json();
  const { name, topic, platform, persona, duration } = body;

  const project = await prisma.project.updateMany({
    where: { id, userId },
    data: { name, topic, platform, persona, duration },
  });

  return NextResponse.json(project);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const authResult = await requireAuth();
  if ("status" in authResult) return authResult;
  const { userId } = authResult;

  const { id } = await params;
  await prisma.project.deleteMany({
    where: { id, userId },
  });

  return NextResponse.json({ success: true });
}
