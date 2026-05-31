"""抓取股價、指數、ETF 資料 — 可單獨執行測試"""
import yfinance as yf
from datetime import date, timedelta
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import CORE_HOLDINGS, WATCHLIST, SECTOR_ETFS, BOTTLENECK_NODES, INDICES, MACRO


def _fetch_quote(ticker: str) -> dict | None:
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="2d")
        if hist.empty or len(hist) < 1:
            return None
        last = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) >= 2 else None
        close = round(float(last["Close"]), 2)
        chg_pct = None
        if prev is not None:
            prev_close = float(prev["Close"])
            chg_pct = round((close - prev_close) / prev_close * 100, 2) if prev_close else None
        volume = int(last["Volume"]) if last["Volume"] else None
        return {"ticker": ticker, "close": close, "chg_pct": chg_pct, "volume": volume}
    except Exception as e:
        print(f"[WARN] {ticker} 抓取失敗: {e}")
        return None


def fetch_core_holdings() -> list[dict]:
    results = []
    for tk in CORE_HOLDINGS + WATCHLIST:
        q = _fetch_quote(tk)
        results.append(q if q else {"ticker": tk, "close": None, "chg_pct": None, "volume": None})
    return results


def fetch_indices() -> list[dict]:
    results = []
    for name, tk in {**INDICES, **MACRO}.items():
        q = _fetch_quote(tk)
        if q:
            q["name"] = name
        else:
            q = {"ticker": tk, "name": name, "close": None, "chg_pct": None, "volume": None}
        results.append(q)
    return results


def fetch_sector_etfs() -> list[dict]:
    results = []
    for name, tk in SECTOR_ETFS.items():
        q = _fetch_quote(tk)
        if q:
            q["name"] = name
        else:
            q = {"ticker": tk, "name": name, "close": None, "chg_pct": None, "volume": None}
        results.append(q)
    return results


def fetch_bottleneck_nodes() -> dict[str, list[dict]]:
    results = {}
    for node, tickers in BOTTLENECK_NODES.items():
        node_data = []
        for tk in tickers:
            q = _fetch_quote(tk)
            node_data.append(q if q else {"ticker": tk, "close": None, "chg_pct": None, "volume": None})
        results[node] = node_data
    return results


if __name__ == "__main__":
    print("=== 核心持股 ===")
    for q in fetch_core_holdings():
        chg = f"{q['chg_pct']:+.2f}%" if q["chg_pct"] is not None else "N/A"
        print(f"  {q['ticker']:8s} ${q['close']}  {chg}")

    print("\n=== 大盤指數 ===")
    for q in fetch_indices():
        chg = f"{q['chg_pct']:+.2f}%" if q["chg_pct"] is not None else "N/A"
        print(f"  {q['name']:20s} {q['close']}  {chg}")
