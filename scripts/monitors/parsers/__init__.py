"""平台解析器注册表

每个平台一个 .py 文件，导出 parse(raw_data) → dict 函数。
解析器通过 monitors.parser.HotContentParser 注册和分发。
"""

# 导入所有平台解析器
from monitors.parsers import douyin
from monitors.parsers import xiaohongshu
from monitors.parsers import bilibili
from monitors.parsers import weibo
from monitors.parsers import zhihu
from monitors.parsers import toutiao
from monitors.parsers import kuaishou
from monitors.parsers import youtube
from monitors.parsers import tiktok
from monitors.parsers import wechat
from monitors.parsers import shipinhao
from monitors.parsers import baidu
from monitors.parsers import instagram

__all__ = [
    "douyin", "xiaohongshu", "bilibili", "weibo", "zhihu",
    "toutiao", "kuaishou", "youtube", "tiktok", "wechat",
    "shipinhao", "baidu", "instagram",
]
