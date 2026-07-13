"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  FileText, 
  MessageSquare, 
  DollarSign,
  ArrowUpRight,
  ArrowDownRight,
  MoreHorizontal
} from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  trend?: "up" | "down" | "neutral";
}

export function StatCard({ title, value, change, changeLabel, icon, trend }: StatCardProps) {
  const trendColor = trend === "up" ? "text-green-500" : trend === "down" ? "text-red-500" : "text-muted-foreground";
  const TrendIcon = trend === "up" ? ArrowUpRight : trend === "down" ? ArrowDownRight : null;

  return (
    <Card className="card-hover">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
          {icon}
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {(change !== undefined || changeLabel) && (
          <div className="flex items-center gap-1 mt-1">
            {TrendIcon && <TrendIcon className={`w-4 h-4 ${trendColor}`} />}
            {change !== undefined && (
              <span className={`text-sm ${trendColor}`}>
                {change > 0 ? "+" : ""}{change}%
              </span>
            )}
            {changeLabel && (
              <span className="text-sm text-muted-foreground">{changeLabel}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface DataTableCardProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}

export function DataTableCard({ title, description, children, action }: DataTableCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </div>
        {action}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

interface ActivityItem {
  id: string;
  type: "comment" | "publish" | "upload" | "subscribe";
  user: string;
  action: string;
  target: string;
  time: string;
}

interface ActivityFeedProps {
  activities: ActivityItem[];
}

export function ActivityFeed({ activities }: ActivityFeedProps) {
  const typeIcons = {
    comment: <MessageSquare className="w-4 h-4" />,
    publish: <FileText className="w-4 h-4" />,
    upload: <FileText className="w-4 h-4" />,
    subscribe: <Users className="w-4 h-4" />,
  };

  const typeColors = {
    comment: "bg-blue-500",
    publish: "bg-green-500",
    upload: "bg-purple-500",
    subscribe: "bg-orange-500",
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>最近动态</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.map((activity) => (
            <div key={activity.id} className="flex items-start gap-3">
              <div className={`w-8 h-8 rounded-full ${typeColors[activity.type]} flex items-center justify-center text-white`}>
                {typeIcons[activity.type]}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm">
                  <span className="font-medium">{activity.user}</span>
                  <span className="text-muted-foreground"> {activity.action} </span>
                  <span className="font-medium">{activity.target}</span>
                </p>
                <p className="text-xs text-muted-foreground">{activity.time}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

interface QuickActionProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  href?: string;
  onClick?: () => void;
  variant?: "default" | "outline" | "ghost";
}

export function QuickAction({ title, description, icon, href, onClick, variant = "outline" }: QuickActionProps) {
  const content = (
    <>
      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary mb-3">
        {icon}
      </div>
      <h3 className="font-medium">{title}</h3>
      <p className="text-sm text-muted-foreground">{description}</p>
    </>
  );

  if (href) {
    return (
      <a href={href} className="block p-4 rounded-lg border hover:bg-muted transition-colors">
        {content}
      </a>
    );
  }

  return (
    <button onClick={onClick} className="block w-full text-left p-4 rounded-lg border hover:bg-muted transition-colors">
      {content}
    </button>
  );
}

interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showPercentage?: boolean;
  variant?: "default" | "success" | "warning" | "danger";
}

export function ProgressBar({ value, max = 100, label, showPercentage = true, variant = "default" }: ProgressBarProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  
  const variantColors = {
    default: "bg-primary",
    success: "bg-green-500",
    warning: "bg-yellow-500",
    danger: "bg-red-500",
  };

  return (
    <div className="space-y-1">
      {(label || showPercentage) && (
        <div className="flex justify-between text-sm">
          {label && <span className="text-muted-foreground">{label}</span>}
          {showPercentage && <span className="font-medium">{Math.round(percentage)}%</span>}
        </div>
      )}
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div 
          className={`h-full ${variantColors[variant]} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

interface StatusBadgeProps {
  status: "active" | "pending" | "error" | "inactive";
  label?: string;
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const variants = {
    active: "bg-green-500/10 text-green-500 border-green-500/20",
    pending: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
    error: "bg-red-500/10 text-red-500 border-red-500/20",
    inactive: "bg-gray-500/10 text-gray-500 border-gray-500/20",
  };

  return (
    <Badge variant="outline" className={variants[status]}>
      {label || status}
    </Badge>
  );
}