"""抓取市場情緒指標 — CNN Fear & Greed"""
import urllib.request
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import FEAR_GREED_URL


def fetch_fear_greed() -> dict | None:
    try:
        req = urllib.request.Request(
            FEAR_GREED_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0 Safari/537.36",
                "Accept": "application/json",
                "Referer": "https://www.cnn.com/",
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        fg = data.get("fear_and_greed", {})
        score = fg.get("score")
        rating = fg.get("rating", "")
        prev = fg.get("previous_close")
        return {
            "score": round(float(score), 1) if score is not None else None,
            "rating": rating,
            "prev_close": round(float(prev), 1) if prev is not None else None,
        }
    except Exception as e:
        print(f"[WARN] Fear & Greed 抓取失敗: {e}")
        return None


def label_fg(score) -> str:
    if score is None:
        return "N/A"
    if score < 20:
        return "😱 極度恐慌"
    if score < 40:
        return "😨 恐慌"
    if score < 60:
        return "😐 中性"
    if score < 80:
        return "😊 貪婪"
    return "🤑 極度貪婪"


if __name__ == "__main__":
    fg = fetch_fear_greed()
    if fg:
        print(f"Fear & Greed: {fg['score']} ({fg['rating']})  昨收: {fg['prev_close']}")
    else:
        print("(資料暫缺)")
