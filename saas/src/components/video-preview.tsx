"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Share2 } from "lucide-react";

interface VideoPreviewProps {
  videoUrl: string;
  title: string;
}

export function VideoPreview({ videoUrl, title }: VideoPreviewProps) {
  const handleCopyLink = () => {
    navigator.clipboard.writeText(videoUrl);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">数字人视频</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <video
          src={videoUrl}
          controls
          className="w-full rounded-lg"
          preload="metadata"
        />
        <div className="flex gap-2">
          <Button variant="outline" size="sm" asChild>
            <a href={videoUrl} download={title}>
              <Download className="mr-2 h-4 w-4" />
              下载
            </a>
          </Button>
          <Button variant="outline" size="sm" onClick={handleCopyLink}>
            <Share2 className="mr-2 h-4 w-4" />
            复制链接
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
