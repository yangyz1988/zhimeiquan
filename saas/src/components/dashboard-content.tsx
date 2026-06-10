"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Plus, FileText, BarChart3, Loader2, Trash2 } from "lucide-react";
import { toast } from "@/components/toaster";

interface Project {
  id: string;
  name: string;
  topic: string;
  platform: string;
  persona: string | null;
  status: string;
  createdAt: string;
  outputs: { fireScore: string | null }[];
}

export function DashboardContent() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [newProject, setNewProject] = useState({ name: "", topic: "", platform: "抖音", persona: "学长型" });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const res = await fetch("/api/projects");
      if (!res.ok) {
        toast("加载项目失败", "error");
        return;
      }
      const data = await res.json();
      setProjects(data);
    } catch (error) {
      console.error(error);
      toast("网络错误，请检查连接", "error");
    } finally {
      setLoading(false);
    }
  };

  const createProject = async () => {
    if (!newProject.name || !newProject.topic) return;
    setCreating(true);
    try {
      const res = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newProject),
      });
      const data = await res.json();
      setProjects([data, ...projects]);
      setShowNew(false);
      setNewProject({ name: "", topic: "", platform: "抖音", persona: "学长型" });
      router.push(`/generate?project=${data.id}`);
    } catch (error) {
      console.error(error);
      toast("创建项目失败", "error");
    } finally {
      setCreating(false);
    }
  };

  const deleteProject = async (id: string) => {
    if (!confirm("确定删除此项目？")) return;
    try {
      await fetch(`/api/projects/${id}`, { method: "DELETE" });
      setProjects(projects.filter((p) => p.id !== id));
      toast("项目已删除", "success");
    } catch (error) {
      console.error(error);
      toast("删除失败", "error");
    }
  };

  const getAvgScore = (outputs: { fireScore: string | null }[]) => {
    const scores = outputs
      .map((o) => {
        if (!o.fireScore) return null;
        try {
          const s = JSON.parse(o.fireScore);
          return s.total || s;
        } catch {
          return null;
        }
      })
      .filter(Boolean);
    if (scores.length === 0) return null;
    return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
  };

  if (loading) {
    return (
      <div className="flex h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">工作台</h1>
          <p className="text-muted-foreground">管理你的内容项目</p>
        </div>
        <Button onClick={() => setShowNew(true)}>
          <Plus className="mr-2 h-4 w-4" />
          新建项目
        </Button>
      </div>

      {showNew && (
        <Card>
          <CardHeader>
            <CardTitle>新建项目</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">项目名称</label>
                <Input
                  placeholder="例如：AI自媒体入门指南"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">内容主题</label>
                <Input
                  placeholder="例如：AI时代普通人如何做自媒体"
                  value={newProject.topic}
                  onChange={(e) => setNewProject({ ...newProject, topic: e.target.value })}
                />
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">目标平台</label>
                <Input
                  value={newProject.platform}
                  onChange={(e) => setNewProject({ ...newProject, platform: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">人设风格</label>
                <Input
                  value={newProject.persona}
                  onChange={(e) => setNewProject({ ...newProject, persona: e.target.value })}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={createProject} disabled={creating}>
                {creating ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                创建
              </Button>
              <Button variant="outline" onClick={() => setShowNew(false)}>取消</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>总项目</CardDescription>
            <CardTitle className="text-2xl">{projects.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>已完成</CardDescription>
            <CardTitle className="text-2xl">
              {projects.filter((p) => p.status === "completed").length}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>平均 Fire Score</CardDescription>
            <CardTitle className="text-2xl text-orange-500">
              {(() => {
                const avg = getAvgScore(projects.flatMap((p) => p.outputs));
                return avg ?? "--";
              })()}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <h2 className="text-xl font-semibold">项目列表</h2>
      {projects.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
            <FileText className="mb-4 h-12 w-12" />
            <p>暂无项目，点击"新建项目"开始创作</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {projects.map((p) => {
            const avgScore = getAvgScore(p.outputs);
            return (
              <Card key={p.id} className="cursor-pointer hover:shadow-md" onClick={() => router.push(`/generate?project=${p.id}`)}>
                <CardContent className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-4">
                    <FileText className="h-8 w-8 text-muted-foreground" />
                    <div>
                      <h3 className="font-medium">{p.name}</h3>
                      <p className="text-sm text-muted-foreground">{p.platform} · {p.topic}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge variant={p.status === "completed" ? "default" : "secondary"}>
                      {p.status === "completed" ? "已完成" : "草稿"}
                    </Badge>
                    {avgScore && (
                      <div className="flex items-center gap-1">
                        <BarChart3 className="h-4 w-4 text-orange-500" />
                        <span className="font-medium">{avgScore}</span>
                      </div>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => { e.stopPropagation(); deleteProject(p.id); }}
                    >
                      <Trash2 className="h-4 w-4 text-muted-foreground" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
