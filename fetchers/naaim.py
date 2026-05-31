"""抓取 NAAIM Exposure Index — 從 naaim.org 解析 Google Charts 資料列"""
import urllib.request
import re


UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}
NAAIM_URL = "https://www.naaim.org/programs/naaim-exposure-index/"


def fetch_naaim() -> dict | None:
    """回傳 {'latest': float, 'date': 'YYYY-MM-DD', 'prev': float} 或 None"""
    try:
        req = urllib.request.Request(NAAIM_URL, headers=UA)
        html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")

        latest = None
        prev = None
        date_str = None

        # 主要:標題錨點「This week's NAAIM Exposure Index number is」後的 shortcode div
        m = re.search(
            r"NAAIM Exposure Index number is[^<]*</h4>\s*<div[^>]*>\s*([\d]{1,3}\.[\d]{1,2})",
            html,
        )
        if m:
            latest = round(float(m.group(1)), 2)

        # 從 Google Charts addRows 取上週值 + 日期 (盡力而為)
        m2 = re.search(r"NAAIM Number'\);\s*data\.addRows\(\[(.*?)\]\);", html, re.DOTALL)
        if m2:
            rows = re.findall(
                r"new Date\((\d+),(\d+),(\d+)\)\s*,\s*([\d.]+)", m2.group(1)
            )
            if rows:
                y, mo, d, val = rows[-1]
                date_str = f"{int(y):04d}-{int(mo)+1:02d}-{int(d):02d}"
                if latest is None:
                    latest = round(float(val), 2)
                if len(rows) >= 2:
                    prev = round(float(rows[-2][3]), 2)

        if latest is not None:
            return {"latest": latest, "date": date_str, "prev": prev}
        return None
    except Exception as e:
        print(f"[WARN] NAAIM 抓取失敗: {e}")
        return None


def label_naaim(v) -> str:
    if v is None:
        return "N/A"
    if v > 100:
        return "過熱(>100)"
    if v >= 80:
        return "偏熱"
    if v < 30:
        return "過冷(<30)"
    return "中性"


if __name__ == "__main__":
    print(fetch_naaim())
