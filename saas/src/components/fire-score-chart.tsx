"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface FireScoreProps {
  hook: number;
  trust: number;
  retention: number;
  conversion: number;
  emotion: number;
  total: number;
  level: string;
}

const dimensions = [
  { key: "hook", label: "钩子力", color: "#f97316" },
  { key: "trust", label: "信任度", color: "#22c55e" },
  { key: "retention", label: "完播力", color: "#3b82f6" },
  { key: "conversion", label: "转化力", color: "#a855f7" },
  { key: "emotion", label: "情绪值", color: "#ec4899" },
] as const;

export function FireScoreChart({ hook, trust, retention, conversion, emotion, total, level }: FireScoreProps) {
  const scores = { hook, trust, retention, conversion, emotion };
  const centerX = 150;
  const centerY = 150;
  const maxRadius = 100;

  const getPoint = (index: number, value: number) => {
    const angle = (Math.PI * 2 * index) / 5 - Math.PI / 2;
    const r = (value / 100) * maxRadius;
    return {
      x: centerX + r * Math.cos(angle),
      y: centerY + r * Math.sin(angle),
    };
  };

  const polygonPoints = dimensions
    .map((d, i) => {
      const p = getPoint(i, scores[d.key as keyof typeof scores]);
      return `${p.x},${p.y}`;
    })
    .join(" ");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Fire Score</span>
          <span className="text-2xl font-bold text-orange-500">{total}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex justify-center">
          <svg width="300" height="300" viewBox="0 0 300 300">
            {[20, 40, 60, 80, 100].map((v) => (
              <polygon
                key={v}
                points={dimensions
                  .map((_, i) => {
                    const p = getPoint(i, v);
                    return `${p.x},${p.y}`;
                  })
                  .join(" ")}
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="1"
              />
            ))}
            {dimensions.map((_, i) => {
              const p = getPoint(i, 100);
              return <line key={i} x1={centerX} y1={centerY} x2={p.x} y2={p.y} stroke="#e5e7eb" strokeWidth="1" />;
            })}
            <polygon points={polygonPoints} fill="rgba(249, 115, 22, 0.2)" stroke="#f97316" strokeWidth="2" />
            {dimensions.map((d, i) => {
              const p = getPoint(i, 115);
              return (
                <text key={d.key} x={p.x} y={p.y} textAnchor="middle" dominantBaseline="middle" className="text-xs fill-muted-foreground">
                  {d.label}
                </text>
              );
            })}
          </svg>
        </div>
        <div className="mt-4 space-y-2">
          {dimensions.map((d) => (
            <div key={d.key} className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full" style={{ backgroundColor: d.color }} />
              <span className="text-sm w-16">{d.label}</span>
              <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${scores[d.key as keyof typeof scores]}%`, backgroundColor: d.color }} />
              </div>
              <span className="text-sm font-medium w-8 text-right">{scores[d.key as keyof typeof scores]}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 text-center">
          <span className="inline-block rounded-full bg-orange-100 px-3 py-1 text-sm font-medium text-orange-800 dark:bg-orange-900/30 dark:text-orange-400">
            {level}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
