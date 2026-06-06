"use client";

import { GenerateForm } from "@/components/generate-form";

export default function GeneratePage() {
  return (
    <div className="container py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">内容生成</h1>
        <p className="text-muted-foreground">输入主题，AI 帮你生成爆款口播内容</p>
      </div>
      <GenerateForm />
    </div>
  );
}
