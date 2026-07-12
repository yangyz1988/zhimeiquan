"""视频号热门解析器"""


def parse(raw_data: dict | list) -> dict:
    """从视频号热门数据提取标题。

    视频号结构（微信 channels API）：
    - DOM: .channel-item .title / .feed-item .desc
    - API: data.feeds[*].media.description
    """
    from monitors.parser import HotContentParser

    titles = []

    feeds = raw_data.get("data", {}).get("feeds", raw_data.get("feeds", []))
    for item in feeds:
        media = item.get("media", {})
        t = media.get("description", media.get("title", item.get("title", "")))
        if t:
            titles.append(str(t).strip())

    dom_items = raw_data.get("dom_items", [])
    for item in dom_items:
        t = item.get("title", item.get("text", ""))
        if t and t not in titles:
            titles.append(str(t).strip())

    return HotContentParser._build_result(titles)
