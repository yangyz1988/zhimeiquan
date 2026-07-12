"""百度热搜解析器"""


def parse(raw_data: dict | list) -> dict:
    """从百度热搜数据提取标题。

    百度热搜页结构：
    - .category-wrap_iQLoo li .title_dIF3B / .content_1YWBm → 标题
    - API: data.cards[*].content[*].word
    """
    from monitors.parser import HotContentParser

    titles = []

    # 从 API JSON 提取
    cards = raw_data.get("data", {}).get("cards", [])
    for card in cards:
        for item in card.get("content", []):
            t = item.get("word", item.get("query", ""))
            if t:
                titles.append(str(t).strip())

    # DOM fallback
    dom_items = raw_data.get("dom_items", [])
    for item in dom_items:
        t = item.get("title", item.get("text", ""))
        if t and t not in titles:
            titles.append(str(t).strip())

    return HotContentParser._build_result(titles)
