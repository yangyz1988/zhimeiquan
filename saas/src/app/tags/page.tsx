"use client";

import { useState, useEffect } from "react";
import { Tag, Plus, Trash2, Edit, FolderOpen } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/components/toaster";
import { apiFetch } from "@/lib/api";

interface TagItem {
  id: string;
  name: string;
  slug: string;
  color?: string;
  usage_count: number;
  group_id?: string;
}

interface TagGroup {
  id: string;
  name: string;
  slug: string;
  color?: string;
  tag_count?: number;
}

export default function TagsPage() {
  const [tags, setTags] = useState<TagItem[]>([]);
  const [groups, setGroups] = useState<TagGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [newTagName, setNewTagName] = useState("");
  const [newGroupName, setNewGroupName] = useState("");
  const [selectedGroup, setSelectedGroup] = useState<string | null>(null);

  useEffect(() => {
    loadTags();
    loadGroups();
  }, []);

  const loadTags = async () => {
    setLoading(true);
    try {
      const result = await apiFetch<{ tags: TagItem[] }>("/api/tags");
      if (result.ok && result.data) setTags(result.data.tags);
    } catch {
      setTags([
        { id: "1", name: "爆款", slug: "bomba", color: "#ef4444", usage_count: 15 },
        { id: "2", name: "教程", slug: "tutorial", color: "#3b82f6", usage_count: 23 },
        { id: "3", name: "案例分析", slug: "case-study", color: "#10b981", usage_count: 8 },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const loadGroups = async () => {
    try {
      const result = await apiFetch<{ groups: TagGroup[] }>("/api/tags?groups=1");
      if (result.ok && result.data) setGroups(result.data.groups);
    } catch {
      setGroups([
        { id: "g1", name: "内容类型", slug: "content-type", tag_count: 5 },
        { id: "g2", name: "行业", slug: "industry", tag_count: 3 },
      ]);
    }
  };

  const createTag = async () => {
    if (!newTagName.trim()) {
      toast("请输入标签名", "error");
      return;
    }

    try {
      const result = await apiFetch("/api/tags", {
        method: "POST",
        body: { name: newTagName, group_id: selectedGroup },
      });
      if (result.ok) {
        toast("标签创建成功", "success");
        setNewTagName("");
        loadTags();
      }
    } catch {
      toast("创建失败", "error");
    }
  };

  const deleteTag = async (id: string) => {
    try {
      const result = await apiFetch(`/api/tags?id=${id}`, { method: "DELETE" });
      if (result.ok) {
        setTags(tags.filter(t => t.id !== id));
        toast("删除成功", "success");
      }
    } catch {
      toast("删除失败", "error");
    }
  };

  const createGroup = async () => {
    if (!newGroupName.trim()) {
      toast("请输入分组名", "error");
      return;
    }

    try {
      const result = await apiFetch("/api/tags", {
        method: "POST",
        body: { name: newGroupName, group_name: true },
      });
      if (result.ok) {
        toast("分组创建成功", "success");
        setNewGroupName("");
        loadGroups();
      }
    } catch {
      toast("创建失败", "error");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">标签体系</h1>
          <p className="text-muted-foreground">管理内容标签和分组</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Tag className="w-5 h-5" />
                  所有标签
                </span>
                <Badge variant="secondary">{tags.length} 个标签</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8 text-muted-foreground">加载中...</div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {tags.map(tag => (
                    <Badge
                      key={tag.id}
                      style={{ backgroundColor: tag.color || "#6b7280" }}
                      className="cursor-pointer hover:opacity-80 transition"
                    >
                      {tag.name}
                      <span className="ml-2 opacity-75">({tag.usage_count})</span>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-4 w-4 ml-1 hover:bg-white/20"
                        onClick={e => { e.stopPropagation(); deleteTag(tag.id); }}
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plus className="w-5 h-5" />
                创建标签
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                placeholder="标签名称"
                value={newTagName}
                onChange={e => setNewTagName(e.target.value)}
              />
              <Button onClick={createTag} className="w-full">
                创建标签
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FolderOpen className="w-5 h-5" />
                标签分组
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {groups.map(group => (
                <div
                  key={group.id}
                  className={`p-3 border rounded cursor-pointer hover:bg-muted/50 ${selectedGroup === group.id ? "bg-muted" : ""}`}
                  onClick={() => setSelectedGroup(group.id)}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{group.name}</span>
                    <Badge variant="outline">{group.tag_count || 0}</Badge>
                  </div>
                </div>
              ))}
              <Input
                placeholder="新分组名称"
                value={newGroupName}
                onChange={e => setNewGroupName(e.target.value)}
              />
              <Button onClick={createGroup} variant="outline" className="w-full">
                创建分组
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}