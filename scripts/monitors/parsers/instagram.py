"""Instagram Explore 解析器"""


def parse(raw_data: dict | list) -> dict:
    """从 Instagram Explore 数据提取标题。

    Instagram Explore 结构：
    - SSR JSON: __INITIAL_STATE__ → explore → items
    - DOM: article a[href] img[alt] → alt 文本作为标题
    """
    from monitors.parser import HotContentParser

    titles = []

    items = raw_data.get("items", raw_data.get("data", []))
    for item in items:
        caption = item.get("caption", {})
        if isinstance(caption, dict):
            t = caption.get("text", item.get("title", ""))
        else:
            t = str(caption) if caption else ""
        if t:
            titles.append(str(t).strip())

    dom_items = raw_data.get("dom_items", [])
    for item in dom_items:
        t = item.get("title", item.get("alt", item.get("text", "")))
        if t and t not in titles:
            titles.append(str(t).strip())

    return HotContentParser._build_result(titles)
