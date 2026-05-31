"""抓取 AAII 散戶情緒。

AAII 官網是 JS 動態渲染,純 Python 無法直接爬。策略:
1. 先試讀本地手動覆寫檔 manual_aaii.json (使用者每週四貼一次最新值)
2. 試爬幾個可能有靜態數據的鏡像來源 (盡力而為)
3. 都失敗 → 回傳 None,報告標「待驗證」(誠實原則,不編造)

manual_aaii.json 範例:
{"bullish": 35.6, "neutral": 22.6, "bearish": 41.9, "date": "2026-05-27"}
"""
import os
import json
import urllib.request
import re


UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}
_HERE = os.path.dirname(os.path.dirname(__file__))
MANUAL_FILE = os.path.join(_HERE, "manual_aaii.json")


def fetch_aaii() -> dict | None:
    """回傳 {'bullish','neutral','bearish','date','source'} 或 None"""
    # 1. 手動覆寫檔優先
    if os.path.exists(MANUAL_FILE):
        try:
            with open(MANUAL_FILE, encoding="utf-8") as f:
                d = json.load(f)
            if "bullish" in d:
                d["source"] = "manual"
                return d
        except Exception as e:
            print(f"[WARN] manual_aaii.json 讀取失敗: {e}")

    # 2. 盡力爬鏡像 (多數會失敗,失敗就跳過)
    for url in [
        "https://www.aaii.com/sentimentsurvey/sent_results",
    ]:
        try:
            req = urllib.request.Request(url, headers=UA)
            html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
            bull = re.search(r"[Bb]ullish[^0-9]{0,30}(\d{1,2}\.\d)", html)
            bear = re.search(r"[Bb]earish[^0-9]{0,30}(\d{1,2}\.\d)", html)
            neut = re.search(r"[Nn]eutral[^0-9]{0,30}(\d{1,2}\.\d)", html)
            if bull and bear:
                return {
                    "bullish": float(bull.group(1)),
                    "neutral": float(neut.group(1)) if neut else None,
                    "bearish": float(bear.group(1)),
                    "date": None,
                    "source": "scrape",
                }
        except Exception:
            pass

    return None


def label_aaii(d) -> str:
    if not d:
        return "N/A"
    bull, bear = d.get("bullish"), d.get("bearish")
    if bull is None or bear is None:
        return "N/A"
    if bear > 50:
        return "極度悲觀(空>50)"
    if bull > 50:
        return "極度樂觀(多>50)"
    return "偏空" if bear > bull else "偏多"


if __name__ == "__main__":
    print(fetch_aaii())
