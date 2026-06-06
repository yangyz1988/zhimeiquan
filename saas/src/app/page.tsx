import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Zap, BarChart3, Globe, Sparkles, Brain, TrendingUp } from "lucide-react";

const features = [
  { icon: Zap, title: "30秒生成爆款内容", desc: "口播稿+字幕+标题+封面，一键搞定" },
  { icon: BarChart3, title: "Fire Score 五维评分", desc: "钩子力/信任度/完播力/转化力/情绪值" },
  { icon: Globe, title: "13平台算法适配", desc: "抖音/小红书/B站/公众号/YouTube/TikTok..." },
  { icon: Brain, title: "6大AI引擎驱动", desc: "文案/配图/脚本/拆解/数据/优化" },
  { icon: TrendingUp, title: "数据回流自动优化", desc: "发布→数据→校准→更准的预测" },
  { icon: Sparkles, title: "一键生成", desc: "输入主题，30秒拿走成品" },
];

const platforms = ["抖音", "小红书", "B站", "公众号", "YouTube", "TikTok", "快手", "微博", "知乎", "头条", "企鹅号", "大鱼号", "百家号"];

export default function Home() {
  return (
    <div className="flex flex-col">
      <section className="container flex flex-col items-center justify-center gap-4 py-24 text-center">
        <div className="rounded-full bg-orange-100 px-4 py-1 text-sm font-medium text-orange-800 dark:bg-orange-900/30 dark:text-orange-400">
          AI 驱动的内容工厂
        </div>
        <h1 className="text-4xl font-bold tracking-tighter sm:text-6xl">
          智媒圈
        </h1>
        <p className="max-w-[600px] text-lg text-muted-foreground">
          输入主题，30秒拿走成品。13平台覆盖，数据驱动。
        </p>
        <div className="flex gap-4">
          <Link href="/generate">
            <Button size="lg">
              <Sparkles className="mr-2 h-4 w-4" />
              开始创作
            </Button>
          </Link>
          <Link href="/monitor">
            <Button variant="outline" size="lg">
              <TrendingUp className="mr-2 h-4 w-4" />
              查看爆款规则
            </Button>
          </Link>
        </div>
      </section>

      <section className="container py-12">
        <h2 className="mb-8 text-center text-3xl font-bold">核心特性</h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <Card key={f.title}>
              <CardHeader>
                <f.icon className="mb-2 h-8 w-8 text-orange-500" />
                <CardTitle>{f.title}</CardTitle>
                <CardDescription>{f.desc}</CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      <section className="container py-12">
        <h2 className="mb-8 text-center text-3xl font-bold">覆盖 13 大平台</h2>
        <div className="flex flex-wrap justify-center gap-3">
          {platforms.map((p) => (
            <div key={p} className="rounded-lg border bg-card px-4 py-2 text-sm font-medium shadow-sm">
              {p}
            </div>
          ))}
        </div>
      </section>

      <section className="container py-24 text-center">
        <h2 className="mb-4 text-3xl font-bold">开始使用智媒圈</h2>
        <p className="mb-8 text-muted-foreground">让普通人也能做出专业级口播内容</p>
        <Link href="/generate">
          <Button size="lg">
            <Zap className="mr-2 h-4 w-4" />
            免费开始
          </Button>
        </Link>
      </section>
    </div>
  );
}
