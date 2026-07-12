"""B站热门解析器"""


def parse(raw_data: dict | list) -> dict:
    """从 B站热门数据提取标题。

    B站热门页结构：
    - .video-card .title → 标题
    - .video-card .play-count → 播放量
    """
    from monitors.parser import HotContentParser

    titles = []

    # 从 items 提取
    items = raw_data.get("items", raw_data.get("data", {}).get("list", []))
    for item in items:
        t = item.get("title", item.get("name", ""))
        if t:
            titles.append(str(t).strip())

    # 从 DOM 提取
    dom_items = raw_data.get("dom_items", [])
    for item in dom_items:
        t = item.get("title", item.get("text", ""))
        if t and t not in titles:
            titles.append(str(t).strip())

    return HotContentParser._build_result(titles)
