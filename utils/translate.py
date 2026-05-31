"""英→繁中翻譯工具(Google 免費端點,免金鑰)

用於把 yfinance 英文新聞標題翻成繁體中文。
- 有本地快取(translate_cache.json)避免重複翻譯
- 失敗時回退原文,絕不讓報告中斷
"""
import os
import json
import urllib.request
import urllib.parse

_HERE = os.path.dirname(os.path.dirname(__file__))
_CACHE_FILE = os.path.join(_HERE, "translate_cache.json")
_cache = None


def _load_cache():
    global _cache
    if _cache is None:
        if os.path.exists(_CACHE_FILE):
            try:
                with open(_CACHE_FILE, encoding="utf-8") as f:
                    _cache = json.load(f)
            except Exception:
                _cache = {}
        else:
            _cache = {}
    return _cache


def _save_cache():
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False, indent=0)
    except Exception:
        pass


def _is_mostly_ascii(s: str) -> bool:
    """已是中文就不翻"""
    non_ascii = sum(1 for ch in s if ord(ch) > 127)
    return non_ascii < len(s) * 0.15


def translate(text: str, tl: str = "zh-TW") -> str:
    if not text or not _is_mostly_ascii(text):
        return text
    cache = _load_cache()
    if text in cache:
        return cache[text]
    try:
        q = urllib.parse.quote(text)
        url = (f"https://translate.googleapis.com/translate_a/single"
               f"?client=gtx&sl=en&tl={tl}&dt=t&q={q}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        out = "".join(seg[0] for seg in data[0] if seg and seg[0])
        if out:
            cache[text] = out
            _save_cache()
            return out
    except Exception:
        pass
    return text  # 失敗回退原文


def translate_news(news_dict: dict) -> dict:
    """翻譯 {ticker: [{title,...}]} 內所有 title,新增 title_zh 欄位"""
    for items in news_dict.values():
        for n in items:
            n["title_zh"] = translate(n.get("title", ""))
    return news_dict


def translate_list(items: list) -> list:
    """翻譯 [{title,...}] 內所有 title"""
    for n in items:
        n["title_zh"] = translate(n.get("title", ""))
    return items


if __name__ == "__main__":
    print(translate("CrowdStrike and Palo Alto Networks Shares Are Soaring"))
    print(translate("這已經是中文，不該被翻譯"))
