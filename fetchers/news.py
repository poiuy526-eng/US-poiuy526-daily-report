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


if __name__ == "__main__":
    news = fetch_stock_news()
    for tk, items in news.items():
        print(f"\n=== {tk} ===")
        for n in items:
            print(f"  [{n['source']}] {n['title']}")
            if n['url']:
                print(f"    {n['url']}")
