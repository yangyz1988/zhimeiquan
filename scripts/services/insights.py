"""内容洞察引擎 - 基于监控数据分析趋势、预测爆款

包含 Moat 4 数据闭环聚合功能：
- get_platform_trends: 按平台聚合数据趋势
- get_best_performing_patterns: 最佳内容模式分析
- get_content_gaps: 内容机会发现
"""

import json
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from monitors.analyzer import RuleAnalyzer
from monitors.scraper import PlatformScraper
from services.logging import logger


class ContentInsightsEngine:
    """内容洞察引擎"""

    PLATFORM_BEST_TIMES = {}
    HOOK_TYPES = []
    TITLE_TYPE_PATTERNS = {}

    def __init__(self, rules_dir=None, analytics_dir=None):
        self.rules_dir = Path(rules_dir or "../data/rules")
        self.analytics_dir = Path(analytics_dir or "../data/analytics")
        self.insights_dir = Path("../data/insights")
        self.insights_dir.mkdir(parents=True, exist_ok=True)
        self.scraper = PlatformScraper()
        self.analyzer = RuleAnalyzer()

    def _load_platform_rules(self, platform):
        fp = self.rules_dir / f"{platform}.json"
        if not fp.exists(): return None
        with open(fp, "r", encoding="utf-8") as f: return json.load(f)

    def analyze_trends(self, platform, days=7):
        rules = self._load_platform_rules(platform)
        if not rules:
            return {"platform": platform, "trends": [], "hot_topics": []}
        hook_patterns = rules.get("hook_patterns", [])
        trending = rules.get("trending_topics", [])
        title_rules = rules.get("title_rules", [])
        trends = [{"type": "hook_pattern", "name": h.get("type", "未知"),
                  "count": h.get("count", 0),
                  "direction": "rising" if h.get("count", 0) > 3 else "stable"}
                 for h in hook_patterns[:5]]
        return {"platform": platform, "trends": trends,
                "hot_topics": trending[:10], "title_patterns": title_rules[:5],
                "summary": f"过去{days}天共分析{len(hook_patterns)}种钩子模式"}

    def predict_viral_topic(self, platform):
        rules = self._load_platform_rules(platform)
        if not rules: return {"platform": platform, "predictions": []}
        trending = rules.get("trending_topics", [])
        hook_patterns = rules.get("hook_patterns", [])
        predictions = []
        for topic in trending[:5]:
            score = min(95, 60 + len(hook_patterns) * 3)
            predictions.append({
                "topic": topic if isinstance(topic, str) else topic.get("title", ""),
                "viral_score": score,
                "reason": f"匹配{len(hook_patterns)}种爆款钩子模式",
                "suggested_hook": hook_patterns[0].get("type", "数字型") if hook_patterns else "数字型",
            })
        return {"platform": platform, "predictions": predictions}

    def get_content_recommendations(self, topic, platform):
        rules = self._load_platform_rules(platform)
        if not rules:
            return {"topic": topic, "platform": platform, "hook_type": "数字型",
                    "best_duration": 60, "title_templates": []}
        hp = rules.get("hook_patterns", [])
        bhook = hp[0].get("type", "数字型") if hp else "数字型"
        return {"topic": topic, "platform": platform, "hook_type": bhook,
                "best_duration": 60,
                "title_templates": rules.get("title_rules", [])[:3],
                "best_practices": rules.get("best_practices", [])[:3]}

    def get_optimal_posting_time(self, platform):
        return {"platform": platform, "time_slots": [],
                "recommendation": f"暂无{platform}的最佳发布时机数据"}

    # ====== Moat 4: 数据闭环聚合 ======

    def _load_analytics_records(self, user_id, days=None):
        records = []
        for f in self.analytics_dir.glob(f"{user_id}_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    r = json.load(fh)
                if days:
                    c = r.get("created_at") or r.get("published_at")
                    if c and (datetime.now() - datetime.fromisoformat(c)) > timedelta(days=days):
                        continue
                records.append(r)
            except Exception as e:
                logger.exception(f"加载记录失败 {f.name}")
        return records

    def _classify_title_type(self, title):
        return "其他"

    def _classify_hook_type(self, title):
        if re.search(r"\d+", title): return "数字型"
        if re.search(r"[?？]", title): return "悬念型"
        if re.search(r"如何|怎么|为什么", title): return "痛点型"
        return "其他"

    def get_platform_trends(self, user_id, days=30):
        records = self._load_analytics_records(user_id, days=days)
        if not records:
            return {"user_id": user_id, "days": days, "platforms": {},
                    "total_records": 0, "summary": "暂无数据",
                    "generated_at": datetime.now().isoformat()}
        pd = {}
        for r in records:
            p = r.get("platform", "未知")
            m = r.get("metrics", {})
            if p not in pd:
                pd[p] = {"total_content": 0, "total_views": 0, "total_likes": 0,
                         "total_comments": 0, "total_shares": 0, "scores": [],
                         "daily_views": defaultdict(int)}
            d = pd[p]
            d["total_content"] += 1
            d["total_views"] += m.get("views", 0)
            d["total_likes"] += m.get("likes", 0)
            d["total_comments"] += m.get("comments", 0)
            d["total_shares"] += m.get("shares", 0)
            if r.get("fire_score"):
                d["scores"].append(r["fire_score"])
            c = r.get("created_at") or r.get("published_at")
            if c: d["daily_views"][c[:10]] += m.get("views", 0)
        rp = {}
        for p, d in pd.items():
            te = d["total_likes"] + d["total_comments"] + d["total_shares"]
            aer = round(te / d["total_views"], 4) if d["total_views"] > 0 else 0.0
            asc = round(sum(d["scores"]) / len(d["scores"]), 1) if d["scores"] else None
            di = sorted(d["daily_views"].items())
            tr = "stable"
            if len(di) >= 4:
                rv = sum(v for _, v in di[-2:])
                ev = sum(v for _, v in di[:2])
                if rv > ev * 1.2: tr = "rising"
                elif rv < ev * 0.8: tr = "declining"
            rp[p] = {"total_content": d["total_content"], "total_views": d["total_views"],
                     "avg_engagement_rate": aer, "avg_fire_score": asc,
                     "trend": tr, "daily_views": dict(sorted(d["daily_views"].items()))}
        res = {"user_id": user_id, "days": days, "platforms": rp,
               "total_records": len(records),
               "summary": f"过去{days}天共发布{len(records)}条内容，覆盖{len(rp)}个平台",
               "generated_at": datetime.now().isoformat()}
        self._save_insight(user_id, "platform_trends", res)
        return res

    def get_best_performing_patterns(self, user_id):
        records = self._load_analytics_records(user_id)
        if not records:
            return {"user_id": user_id, "patterns": {}, "summary": "暂无数据",
                    "generated_at": datetime.now().isoformat()}
        ttp = defaultdict(list)
        hkp = defaultdict(list)
        hrp = defaultdict(list)
        for r in records:
            m = r.get("metrics", {})
            v = m.get("views", 0)
            if v < 10: continue
            eng = (m.get("likes", 0) + m.get("comments", 0) + m.get("shares", 0)) / v
            title = r.get("title", "")
            ttp[self._classify_title_type(title)].append(eng)
            hkp[self._classify_hook_type(title)].append(eng)
            c = r.get("created_at") or r.get("published_at")
            if c:
                try: hrp[datetime.fromisoformat(c).hour].append(eng)
                except (ValueError, TypeError):
                    logger.debug(f"无法解析时间戳 {c}", exc_info=True)

        def cs(pd):
            return sorted([{"name": k, "avg_engagement": round(sum(v)/len(v), 4),
                           "sample_count": len(v)}
                          for k, v in pd.items() if v],
                         key=lambda x: x["avg_engagement"], reverse=True)

        bh = sorted([{"hour": f"{h:02d}:00", "avg_engagement": round(sum(v)/len(v), 4),
                     "sample_count": len(v)}
                    for h, v in hrp.items() if v],
                   key=lambda x: x["avg_engagement"], reverse=True)

        hp = [{"title": r.get("title", ""), "platform": r.get("platform", ""),
                "engagement_rate": round((m.get("likes", 0)+m.get("comments", 0)+m.get("shares", 0))/m.get("views", 1), 4),
                "views": m.get("views", 0), "fire_score": r.get("fire_score")}
              for r in records if (m:=r.get("metrics", {})).get("views", 0) >= 100
              and (m.get("likes", 0)+m.get("comments", 0)+m.get("shares", 0))/m.get("views", 1) > 0.1]
        hp.sort(key=lambda x: x["engagement_rate"], reverse=True)

        patterns = {"best_title_types": cs(ttp)[:5], "best_hook_types": cs(hkp)[:5],
                    "best_posting_hours": bh[:5], "high_performance_content": hp[:10]}
        res = {"user_id": user_id, "patterns": patterns,
               "summary": self._generate_pattern_summary(patterns),
               "generated_at": datetime.now().isoformat()}
        self._save_insight(user_id, "best_patterns", res)
        return res

    def _generate_pattern_summary(self, patterns):
        parts = []
        if patterns.get("best_title_types"):
            b = patterns["best_title_types"][0]
            parts.append(f"最佳标题类型: {b['name']} ({b['avg_engagement']:.2%})")
        if patterns.get("best_hook_types"):
            parts.append(f"最佳钩子类型: {patterns['best_hook_types'][0]['name']}")
        if patterns.get("best_posting_hours"):
            parts.append(f"最佳发布时间: {patterns['best_posting_hours'][0]['hour']}")
        if patterns.get("high_performance_content"):
            parts.append(f"高互动内容: {len(patterns['high_performance_content'])}条")
        return " | ".join(parts) if parts else "暂无足够数据"

    def get_content_gaps(self, user_id):
        records = self._load_analytics_records(user_id)
        ut = set()
        for r in records:
            ut.update(re.findall(r"[\w一-鿿]{2,}", r.get("title", "")))
        ct = {}
        for rf in self.rules_dir.glob("*.json"):
            try:
                with open(rf, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                p = rules.get("platform", rf.stem)
                for t in rules.get("trending_topics", []):
                    ts = t if isinstance(t, str) else t.get("title", "")
                    if ts not in ct:
                        ct[ts] = {"count": 0, "platforms": [], "viral_score": 0}
                    ct[ts]["count"] += 1
                    if p not in ct[ts]["platforms"]:
                        ct[ts]["platforms"].append(p)
                    if isinstance(t, dict):
                        ct[ts]["viral_score"] = max(ct[ts]["viral_score"], t.get("viral_score", 0))
                    else:
                        ct[ts]["viral_score"] += 5
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"加载规则文件失败 {rf.name}", error=str(e))

        gaps = [{"topic": t, "mentions": i["count"], "platforms": i["platforms"],
                 "viral_score": min(i["viral_score"], 100),
                 "opportunity_score": round(min(i["count"]*10 + i["viral_score"]/2, 100), 1)}
                for t, i in ct.items()
                if i["count"] >= 2 and not (any(kw in t for kw in ut) or any(t in kw for kw in ut))]
        gaps.sort(key=lambda x: x["opportunity_score"], reverse=True)

        hp = [g for g in gaps if g["opportunity_score"] >= 60]
        mp = [g for g in gaps if 30 <= g["opportunity_score"] < 60]
        lp = [g for g in gaps if g["opportunity_score"] < 30]

        res = {"user_id": user_id, "user_topic_count": len(ut),
               "competitor_topic_count": len(ct), "gap_count": len(gaps),
               "content_gaps": {"high_priority": hp[:10], "medium_priority": mp[:10], "low_priority": lp[:10]},
               "recommendations": [f"建议创作关于'{g['topic']}'的内容" for g in hp[:5]],
               "generated_at": datetime.now().isoformat()}
        self._save_insight(user_id, "content_gaps", res)
        return res

    def _save_insight(self, user_id, insight_type, data):
        try:
            fp = self.insights_dir / f"{user_id}_{insight_type}.json"
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.exception(f"保存洞察结果失败: {e}")
