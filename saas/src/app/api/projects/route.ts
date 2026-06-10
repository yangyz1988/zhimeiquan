import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export async function GET() {
  const authResult = await requireAuth();
  if ("status" in authResult) return authResult;
  const { userId } = authResult;

  const projects = await prisma.project.findMany({
    where: { userId },
    orderBy: { createdAt: "desc" },
    include: { outputs: true },
  });

  return NextResponse.json(projects);
}

export async function POST(request: NextRequest) {
  const authResult = await requireAuth();
  if ("status" in authResult) return authResult;
  const { userId } = authResult;

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
