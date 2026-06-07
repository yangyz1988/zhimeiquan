"""平台采集器测试"""

import pytest
from monitors.scraper import PlatformScraper


def test_scraper_has_platforms():
    scraper = PlatformScraper()
    platforms = scraper.get_supported_platforms()
    assert len(platforms) >= 7


def test_scraper_includes_mainstream_platforms():
    scraper = PlatformScraper()
    platforms = scraper.get_supported_platforms()
    names = {p["name"] for p in platforms}
    assert "抖音" in names
    assert "小红书" in names
    assert "B站" in names
    assert "微博" in names
    assert "知乎" in names


def test_scraper_platform_categories():
    scraper = PlatformScraper()
    platforms = scraper.get_supported_platforms()
    for p in platforms:
        assert "name" in p
        assert "category" in p
        assert p["category"]


def test_scraper_parse_douyin():
    scraper = PlatformScraper()
    data = {
        "data": {
            "word_list": [
                {"word": "AI 智能", "hot_value": 1234567, "word_type": "科技"},
                {"word": "美食分享", "hot_value": 999999, "word_type": "生活"},
            ]
        }
    }
    results = scraper._parse_hot_list("抖音", data)
    assert len(results) == 2
    assert results[0]["title"] == "AI 智能"
    assert results[0]["heat"] == 1234567
    assert results[0]["category"] == "短视频"


def test_scraper_parse_bilibili():
    scraper = PlatformScraper()
    data = {
        "data": {
            "list": [
                {"title": "测试视频", "stat": {"view": 10000}, "tname": "知识"},
            ]
        }
    }
    results = scraper._parse_hot_list("B站", data)
    assert len(results) == 1
    assert results[0]["heat"] == 10000
    assert results[0]["category"] == "中长视频"


def test_scraper_parse_weibo():
    scraper = PlatformScraper()
    data = {
        "data": {
            "realtime": [
                {"note": "热搜话题", "num": 9999, "category": "娱乐"},
            ]
        }
    }
    results = scraper._parse_hot_list("微博", data)
    assert len(results) == 1
    assert results[0]["heat"] == 9999


def test_scraper_parse_zhihu():
    scraper = PlatformScraper()
    data = {"data": [{"target": {"title": "热门问题"}, "detail_text": "1000万热度"}]}
    results = scraper._parse_hot_list("知乎", data)
    assert len(results) == 1
    assert results[0]["title"] == "热门问题"
    assert results[0]["heat"] == "1000万热度"


def test_scraper_parse_toutiao():
    scraper = PlatformScraper()
    data = {"data": [{"Title": "今日头条", "HotValue": 888888, "Category": "新闻"}]}
    results = scraper._parse_hot_list("头条", data)
    assert len(results) == 1
    assert results[0]["title"] == "今日头条"
    assert results[0]["heat"] == 888888


def test_scraper_parse_baidu():
    scraper = PlatformScraper()
    data = {
        "data": {
            "cards": [
                {
                    "content": [
                        {"word": "百度热搜词", "hotScore": 777777, "desc": "热点"}
                    ]
                }
            ]
        }
    }
    results = scraper._parse_hot_list("百度热搜", data)
    assert len(results) == 1
    assert results[0]["heat"] == 777777


def test_scraper_parse_unknown_platform():
    scraper = PlatformScraper()
    results = scraper._parse_hot_list("未知平台", {"data": []})
    assert results == []


def test_scraper_parse_filters_empty_titles():
    scraper = PlatformScraper()
    data = {
        "data": {
            "word_list": [
                {"word": "", "hot_value": 100},
                {"word": "有效词", "hot_value": 200},
            ]
        }
    }
    results = scraper._parse_hot_list("抖音", data)
    assert len(results) == 1
    assert results[0]["title"] == "有效词"


def test_scraper_handles_non_dict_data():
    scraper = PlatformScraper()
    assert scraper._parse_hot_list("抖音", "string") == []
    assert scraper._parse_hot_list("抖音", []) == []
    assert scraper._parse_hot_list("抖音", None) == []


def test_scraper_close():
    import asyncio

    scraper = PlatformScraper()
    asyncio.run(scraper.close())


def test_scraper_request_count():
    scraper = PlatformScraper()
    assert scraper._request_count == 0
