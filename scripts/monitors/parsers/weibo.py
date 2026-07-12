"""微博热搜解析器"""


def parse(raw_data: dict | list) -> dict:
    """从微博热搜数据提取标题。

    微博 /ajax/side/hotSearch 返回 JSON:
    { data: { realtime: [ { note, num, category }, ... ] } }
    """
    from monitors.parser import HotContentParser

    titles = []

    realtime = raw_data.get("data", {}).get("realtime", [])
    for item in realtime:
        note = item.get("note", item.get("word", ""))
        if note:
            titles.append(str(note).strip())

    # DOM fallback
    dom_items = raw_data.get("dom_items", [])
    for item in dom_items:
        t = item.get("title", item.get("text", ""))
        if t and t not in titles:
            titles.append(str(t).strip())

    return HotContentParser._build_result(titles)
