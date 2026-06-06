import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "未登录" }, { status: 401 });
  }

  const projects = await prisma.project.findMany({
    where: { userId },
    orderBy: { createdAt: "desc" },
    include: { outputs: true },
  });

  return NextResponse.json(projects);
}

export async function POST(request: NextRequest) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "未登录" }, { status: 401 });
  }

  const body = await request.json();
  const { name, topic, platform, persona, duration } = body;

  const project = await prisma.project.create({
    data: {
      name,
      topic,
      platform,
      persona,
      duration,
      userId,
    },
  });

  return NextResponse.json(project);
}
