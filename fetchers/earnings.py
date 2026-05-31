"""抓取財報日期 — 用 yfinance calendar"""
import yfinance as yf
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import CORE_HOLDINGS, WATCHLIST


def fetch_earnings_dates(tickers: list[str] = None) -> list[dict]:
    """回傳 [{'ticker','date'}] 依日期排序;抓不到的略過"""
    if tickers is None:
        tickers = CORE_HOLDINGS + WATCHLIST
    out = []
    for tk in tickers:
        try:
            cal = yf.Ticker(tk).calendar
            ed = cal.get("Earnings Date") if isinstance(cal, dict) else None
            if ed:
                d = ed[0] if isinstance(ed, list) else ed
                if isinstance(d, date):
                    out.append({"ticker": tk, "date": d})
        except Exception as e:
            print(f"[WARN] {tk} 財報日抓取失敗: {e}")
    out.sort(key=lambda x: x["date"])
    return out


if __name__ == "__main__":
    for e in fetch_earnings_dates():
        print(f"  {e['date']}  {e['ticker']}")
