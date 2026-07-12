"""头条热榜解析器"""


def parse(raw_data: dict | list) -> dict:
    """从头条热榜数据提取标题。

    头条热榜结构：
    - SSR JSON: __TOUTIAO_STATE__ → hotBoard → items
    - DOM: .feed-card .title
    """
    from monitors.parser import HotContentParser

    titles = []

    items = raw_data.get("items", raw_data.get("data", []))
    for item in items:
        t = item.get("Title", item.get("title", item.get("word", "")))
        if t:
            titles.append(str(t).strip())

    dom_items = raw_data.get("dom_items", [])
    for item in dom_items:
        t = item.get("title", item.get("text", ""))
        if t and t not in titles:
            titles.append(str(t).strip())

    return HotContentParser._build_result(titles)
