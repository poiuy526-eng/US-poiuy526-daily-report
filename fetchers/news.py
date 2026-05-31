"""抓取個股新聞 — yfinance"""
import yfinance as yf
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import NEWS_TICKERS


def fetch_stock_news(tickers: list[str] = None, max_per_ticker: int = 3) -> dict[str, list[dict]]:
    if tickers is None:
        tickers = NEWS_TICKERS
    result = {}
    for tk in tickers:
        try:
            t = yf.Ticker(tk)
            raw = t.news or []
            items = []
            for n in raw[:max_per_ticker]:
                content = n.get("content", {})
                title = content.get("title") or n.get("title", "")
                url = ""
                cp = content.get("canonicalUrl", {})
                if isinstance(cp, dict):
                    url = cp.get("url", "")
                if not url:
                    url = n.get("link", "")
                provider = ""
                prov = content.get("provider", {})
                if isinstance(prov, dict):
                    provider = prov.get("displayName", "")
                if title:
                    items.append({"title": title, "url": url, "source": provider})
            result[tk] = items
        except Exception as e:
            print(f"[WARN] {tk} 新聞抓取失敗: {e}")
            result[tk] = []
    return result


def fetch_market_news(max_items: int = 6) -> list[dict]:
    """抓大盤/總經新聞(SPY+QQQ 去重)"""
    seen = set()
    out = []
    for tk in ["SPY", "QQQ"]:
        try:
            for n in (yf.Ticker(tk).news or []):
                content = n.get("content", {})
                title = content.get("title") or n.get("title", "")
                if not title or title in seen:
                    continue
                seen.add(title)
                url = ""
                cp = content.get("canonicalUrl", {})
                if isinstance(cp, dict):
                    url = cp.get("url", "")
                if not url:
                    url = n.get("link", "")
                prov = content.get("provider", {})
                src = prov.get("displayName", "") if isinstance(prov, dict) else ""
                out.append({"title": title, "url": url, "source": src})
        except Exception as e:
            print(f"[WARN] {tk} 大盤新聞抓取失敗: {e}")
    return out[:max_items]


if __name__ == "__main__":
    print("=== 大盤新聞 ===")
    for n in fetch_market_news():
        print(f"  [{n['source']}] {n['title']}")
    print("\n=== 個股新聞 ===")
    news = fetch_stock_news()
    for tk, items in news.items():
        print(f"\n=== {tk} ===")
        for n in items:
            print(f"  [{n['source']}] {n['title']}")
            if n['url']:
                print(f"    {n['url']}")
