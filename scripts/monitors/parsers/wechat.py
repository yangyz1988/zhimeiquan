"""公众号热文解析器"""


def parse(raw_data: dict | list) -> dict:
    """从公众号/搜狗微信热文提取标题。

    搜狗微信结构：.news-list .news-item → .txt-box h3 → 标题
    """
    from monitors.parser import HotContentParser

    titles = []

    items = raw_data.get("items", raw_data.get("data", []))
    for item in items:
        t = item.get("title", item.get("name", ""))
        if t:
            titles.append(str(t).strip())

    dom_items = raw_data.get("dom_items", [])
    for item in dom_items:
        t = item.get("title", item.get("text", ""))
        if t and t not in titles:
            titles.append(str(t).strip())

    return HotContentParser._build_result(titles)
