"""小红书热搜解析器"""


def parse(raw_data: dict | list) -> dict:
    """从小红书热搜数据提取标题。

    小红书 explore 页结构：
    - SSR JSON: __INITIAL_STATE__ → note items
    - DOM: .note-item .title / .note-item .desc
    """
    from monitors.parser import HotContentParser

    titles = []

    # 从 note items 提取
    items = raw_data.get("items", raw_data.get("note_list", raw_data.get("data", {}).get("items", [])))
    for item in items:
        t = item.get("title", item.get("desc", item.get("content", "")))
        if t:
            titles.append(str(t).strip())

    # 从 DOM 提取
    dom_items = raw_data.get("dom_items", [])
    for item in dom_items:
        t = item.get("title", item.get("text", ""))
        if t and t not in titles:
            titles.append(str(t).strip())

    return HotContentParser._build_result(titles)
