"""TikTok Trending 解析器"""


def parse(raw_data: dict | list) -> dict:
    """从 TikTok Trending 数据提取标题。

    TikTok 反爬较强，通常需要 JS 渲染后提取。
    结构：
    - DOM: .tiktok-feed [data-e2e] → desc
    - SSR: script[type="application/json"] → item data
    """
    from monitors.parser import HotContentParser

    titles = []

    items = raw_data.get("items", raw_data.get("itemList", []))
    for item in items:
        t = item.get("desc", item.get("title", item.get("text", "")))
        if t:
            titles.append(str(t).strip())

    dom_items = raw_data.get("dom_items", [])
    for item in dom_items:
        t = item.get("title", item.get("text", ""))
        if t and t not in titles:
            titles.append(str(t).strip())

    return HotContentParser._build_result(titles)
