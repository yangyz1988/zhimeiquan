"use client";

import { useState, useEffect } from "react";
import { Upload, FolderOpen, Image, Video, Music, FileText, Trash2, Search } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/components/toaster";
import { apiFetch } from "@/lib/api";

interface Asset {
  id: string;
  file_name: string;
  original_name?: string;
  mime_type: string;
  size: number;
  url: string;
  thumbnail_url?: string;
  folder?: string;
  tags?: string[];
  created_at: string;
}

export default function MediaPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [folder, setFolder] = useState("default");
  const [search, setSearch] = useState("");
  const [view, setView] = useState<"grid" | "list">("grid");

  useEffect(() => {
    loadAssets();
  }, [folder]);

  const loadAssets = async () => {
    setLoading(true);
    try {
      const result = await apiFetch<{ assets: Asset[]; total: number }>(
        `/api/media?folder=${folder}`
      );
      if (result.ok && result.data) {
        setAssets(result.data.assets);
      }
    } catch {
      // Demo data
      setAssets([
        { id: "1", file_name: "cover.png", mime_type: "image/png", size: 1024000, url: "/placeholder.png", folder: "default", created_at: new Date().toISOString() },
        { id: "2", file_name: "video.mp4", mime_type: "video/mp4", size: 10240000, url: "/placeholder.mp4", folder: "default", created_at: new Date().toISOString() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    toast("上传功能需要对接文件存储服务", "info");
  };

  const handleDelete = async (id: string) => {
    try {
      const result = await apiFetch(`/api/media?asset_id=${id}`, { method: "DELETE" });
      if (result.ok) {
        setAssets(assets.filter(a => a.id !== id));
        toast("删除成功", "success");
      }
    } catch {
      toast("删除失败", "error");
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getIcon = (mime: string) => {
    if (mime.startsWith("image")) return <Image className="w-8 h-8" />;
    if (mime.startsWith("video")) return <Video className="w-8 h-8" />;
    if (mime.startsWith("audio")) return <Music className="w-8 h-8" />;
    return <FileText className="w-8 h-8" />;
  };

  const filtered = assets.filter(a =>
    a.file_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">媒体资产管理</h1>
          <p className="text-muted-foreground">管理图片、视频、音频等媒体文件</p>
        </div>
        <Button onClick={handleUpload}>
          <Upload className="w-4 h-4 mr-2" />
          上传文件
        </Button>
      </div>

      <div className="flex gap-4 items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="搜索文件..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Button variant={folder === "default" ? "default" : "outline"} size="sm" onClick={() => setFolder("default")}>
            <FolderOpen className="w-4 h-4 mr-1" /> 全部
          </Button>
          <Button variant={folder === "images" ? "default" : "outline"} size="sm" onClick={() => setFolder("images")}>
            <Image className="w-4 h-4 mr-1" /> 图片
          </Button>
          <Button variant={folder === "videos" ? "default" : "outline"} size="sm" onClick={() => setFolder("videos")}>
            <Video className="w-4 h-4 mr-1" /> 视频
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>文件列表</span>
            <Badge variant="secondary">{filtered.length} 个文件</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12 text-muted-foreground">加载中...</div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Upload className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>暂无媒体文件</p>
              <p className="text-sm">点击上方按钮上传</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {filtered.map(asset => (
                <div key={asset.id} className="group relative border rounded-lg p-3 hover:shadow-md transition">
                  <div className="aspect-square bg-muted rounded flex items-center justify-center mb-2">
                    {getIcon(asset.mime_type)}
                  </div>
                  <p className="text-sm font-medium truncate">{asset.original_name || asset.file_name}</p>
                  <p className="text-xs text-muted-foreground">{formatSize(asset.size)}</p>
                  <Button
                    variant="destructive"
                    size="icon"
                    className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition"
                    onClick={() => handleDelete(asset.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}