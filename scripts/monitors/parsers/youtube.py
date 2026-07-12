"""YouTube Trending 解析器"""


def parse(raw_data: dict | list) -> dict:
    """从 YouTube Trending 数据提取标题。

    YouTube Trending 结构：
    - ytd-video-renderer #video-title → 标题
    - SSR JSON: ytInitialData → contents → items
    """
    from monitors.parser import HotContentParser

    titles = []

    items = raw_data.get("items", raw_data.get("contents", []))
    for item in items:
        # YouTube 的嵌套结构
        for sub in item.get("items", [item]):
            t = sub.get("title", sub.get("headline", ""))
            if t:
                titles.append(str(t).strip())

    dom_items = raw_data.get("dom_items", [])
    for item in dom_items:
        t = item.get("title", item.get("text", ""))
        if t and t not in titles:
            titles.append(str(t).strip())

    return HotContentParser._build_result(titles)
