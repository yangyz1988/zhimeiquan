"use client";

import { useState, useEffect } from "react";
import { MessageSquare, Send, Check, X, Reply } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/components/toaster";
import { apiFetch } from "@/lib/api";

interface Comment {
  id: string;
  user_id: string;
  body: string;
  is_resolved: boolean;
  parent_id?: string;
  entity_type: string;
  entity_id: string;
  created_at: string;
  children?: Comment[];
}

export default function CommentsPage() {
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState("");
  const [entityType, setEntityType] = useState("content");
  const [entityId, setEntityId] = useState("demo-1");

  useEffect(() => {
    loadComments();
  }, [entityType, entityId]);

  const loadComments = async () => {
    setLoading(true);
    try {
      const result = await apiFetch<{ comments: Comment[] }>(
        `/api/comments?entity_type=${entityType}&entity_id=${entityId}`
      );
      if (result.ok && result.data) {
        setComments(result.data.comments);
      }
    } catch {
      setComments([
        { id: "1", user_id: "user1", body: "这个标题可以更有吸引力", is_resolved: false, entity_type: "content", entity_id: "demo-1", created_at: new Date().toISOString(), children: [
          { id: "2", user_id: "user2", body: "同意，建议用数字式标题", is_resolved: false, entity_type: "content", entity_id: "demo-1", parent_id: "1", created_at: new Date().toISOString() }
        ]},
        { id: "3", user_id: "user3", body: "封面图需要调整", is_resolved: true, entity_type: "content", entity_id: "demo-1", created_at: new Date().toISOString() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!newComment.trim()) {
      toast("请输入评论内容", "error");
      return;
    }

    try {
      const result = await apiFetch("/api/comments", {
        method: "POST",
        body: { body: newComment, entity_type: entityType, entity_id: entityId },
      });
      if (result.ok) {
        toast("评论已提交", "success");
        setNewComment("");
        loadComments();
      }
    } catch {
      toast("提交失败", "error");
    }
  };

  const handleResolve = async (id: string, resolved: boolean) => {
    try {
      const result = await apiFetch(`/api/comments?id=${id}`, {
        method: "PATCH",
        body: { is_resolved: resolved },
      });
      if (result.ok) {
        setComments(comments.map(c =>
          c.id === id ? { ...c, is_resolved: resolved } : c
        ));
        toast(resolved ? "已标记解决" : "已重新打开", "success");
      }
    } catch {
      toast("操作失败", "error");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const result = await apiFetch(`/api/comments?id=${id}`, { method: "DELETE" });
      if (result.ok) {
        setComments(comments.filter(c => c.id !== id));
        toast("删除成功", "success");
      }
    } catch {
      toast("删除失败", "error");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">协作评论</h1>
          <p className="text-muted-foreground">团队协作评论和反馈</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                评论列表
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {loading ? (
                <div className="text-center py-8 text-muted-foreground">加载中...</div>
              ) : comments.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>暂无评论</p>
                </div>
              ) : (
                comments.map(comment => (
                  <div key={comment.id} className={`border rounded-lg p-4 ${comment.is_resolved ? "bg-muted/50" : ""}`}>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-sm font-bold">
                          {comment.user_id.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-medium">{comment.user_id}</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(comment.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {comment.is_resolved && <Badge variant="secondary">已解决</Badge>}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleResolve(comment.id, !comment.is_resolved)}
                        >
                          {comment.is_resolved ? <X className="w-4 h-4" /> : <Check className="w-4 h-4" />}
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(comment.id)}>
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    <p className="text-sm">{comment.body}</p>

                    {comment.children && comment.children.length > 0 && (
                      <div className="mt-3 ml-6 space-y-2 border-l-2 pl-3">
                        {comment.children.map(child => (
                          <div key={child.id} className="bg-muted/30 rounded p-2">
                            <p className="text-xs font-medium">{child.user_id}</p>
                            <p className="text-sm">{child.body}</p>
                          </div>
                        ))}
                      </div>
                    )}

                    <Button variant="ghost" size="sm" className="mt-2">
                      <Reply className="w-4 h-4 mr-1" /> 回复
                    </Button>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle>发表评论</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="输入评论内容..."
                value={newComment}
                onChange={e => setNewComment(e.target.value)}
                rows={4}
              />
              <Button onClick={handleSubmit} className="w-full">
                <Send className="w-4 h-4 mr-2" />
                提交评论
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}