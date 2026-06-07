-- 智媒圈 PostgreSQL Schema
-- 用于 Docker 部署或生产环境

CREATE DATABASE zhimeiquan;
\c zhimeiquan;

CREATE TABLE IF NOT EXISTS "User" (
    id TEXT PRIMARY KEY,
    "clerkId" TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    imageUrl TEXT,
    plan TEXT DEFAULT 'free',
    "stripeCustomerId" TEXT,
    "createdAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "Project" (
    id TEXT PRIMARY KEY,
    "userId" TEXT NOT NULL REFERENCES "User"(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    topic TEXT,
    platform TEXT,
    status TEXT DEFAULT 'draft',
    "fireScore" JSONB,
    tags JSONB,
    "createdAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "Output" (
    id TEXT PRIMARY KEY,
    "projectId" TEXT NOT NULL REFERENCES "Project"(id) ON DELETE CASCADE,
    "contentType" TEXT NOT NULL,
    title TEXT,
    content TEXT,
    "videoUrl" TEXT,
    "imageUrl" TEXT,
    metadata JSONB,
    "createdAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_project_user ON "Project"("userId");
CREATE INDEX idx_output_project ON "Output"("projectId");
CREATE INDEX idx_user_clerk ON "User"("clerkId");
