"""抖音热搜解析器"""


def parse(raw_data: dict | list) -> dict:
    """从抖音热搜数据提取标题。

    raw_data 是 Playwright 从页面提取的原始数据。
    抖音热搜页结构：
    - SSR JSON: data["word_list"][*]["word"]
    - DOM: items[*]["title"]
    """
    from monitors.parser import HotContentParser

    titles = []

    # 从 word_list 提取
    word_list = raw_data.get("word_list", raw_data.get("data", {}).get("word_list", []))
    for item in word_list:
        word = item.get("word", item.get("title", ""))
        if word:
            titles.append(str(word).strip())

    # 从 DOM 提取
    hot_items = raw_data.get("dom_items", [])
    for item in hot_items:
        t = item.get("title", item.get("text", ""))
        if t and t not in titles:
            titles.append(str(t).strip())

    return HotContentParser._build_result(titles)
