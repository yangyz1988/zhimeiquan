"""知乎热榜解析器"""


def parse(raw_data: dict | list) -> dict:
    """从知乎热榜数据提取标题。

    知乎热榜结构：
    .HotList-list .HotItem-content → .HotItem-title → 标题
    """
    from monitors.parser import HotContentParser

    titles = []

    # 从 items 提取
    items = raw_data.get("items", raw_data.get("data", []))
    for item in items:
        target = item.get("target", {})
        t = target.get("title", item.get("title", ""))
        if t:
            titles.append(str(t).strip())

    # DOM fallback
    dom_items = raw_data.get("dom_items", [])
    for item in dom_items:
        t = item.get("title", item.get("text", ""))
        if t and t not in titles:
            titles.append(str(t).strip())

    return HotContentParser._build_result(titles)
