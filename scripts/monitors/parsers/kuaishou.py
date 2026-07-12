"""快手热门解析器"""


def parse(raw_data: dict | list) -> dict:
    """从快手热门数据提取标题。

    快手热门页结构：
    - SSR JSON: __APOLLO_STATE__ → video items
    - DOM: .video-card .title / .video-item .caption
    """
    from monitors.parser import HotContentParser

    titles = []

    items = raw_data.get("items", raw_data.get("data", {}).get("visionVideoList", []))
    for item in items:
        photo = item.get("photo", {})
        t = photo.get("caption", item.get("title", ""))
        if t:
            titles.append(str(t).strip())

    dom_items = raw_data.get("dom_items", [])
    for item in dom_items:
        t = item.get("title", item.get("text", ""))
        if t and t not in titles:
            titles.append(str(t).strip())

    return HotContentParser._build_result(titles)
