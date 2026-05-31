"""FRED 總經數據 — 三層回退設計

1. 若設環境變數 FRED_API_KEY → 用官方 API(最穩,計算 YoY)
   免費金鑰申請:https://fredaccount.stlouisfed.org/apikeys
2. 否則試 fredgraph.csv 免金鑰端點
3. 都失敗 → 讀本地 manual_macro.json(使用者手動維護)
4. 再不行 → 回傳 None,報告標「待補」(誠實原則)
"""
import os
import json
import urllib.request

_HERE = os.path.dirname(os.path.dirname(__file__))
MANUAL_FILE = os.path.join(_HERE, "manual_macro.json")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"}

# 要抓的指標:series_id → (中文名, 是否算年增 YoY)
SERIES = {
    "CPIAUCSL": ("CPI 年增", True),
    "CPILFESL": ("核心 CPI 年增", True),
    "PCEPI": ("PCE 年增", True),
    "PCEPILFE": ("核心 PCE 年增", True),
    "UNRATE": ("失業率", False),
    "FEDFUNDS": ("聯邦基金利率", False),
}


def _api_observations(series_id, api_key, limit=14):
    url = (f"https://api.stlouisfed.org/fred/series/observations"
           f"?series_id={series_id}&api_key={api_key}&file_type=json"
           f"&sort_order=desc&limit={limit}")
    req = urllib.request.Request(url, headers=UA)
    data = json.loads(urllib.request.urlopen(req, timeout=15).read())
    obs = [(o["date"], float(o["value"])) for o in data.get("observations", [])
           if o.get("value") not in (".", None, "")]
    return obs  # 由新到舊


def _csv_observations(series_id, limit=14):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    req = urllib.request.Request(url, headers=UA)
    txt = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    # 驗證是 CSV(第一行含逗號的 header),避免錯誤 HTML 頁被誤解析
    lines = txt.strip().split("\n")
    if not lines or "," not in lines[0] or "<" in txt[:200]:
        raise ValueError("非預期的 FRED CSV 回應")
    obs = []
    for r in lines[1:]:
        parts = r.split(",")
        if len(parts) != 2:
            continue
        d, v = parts
        if v not in (".", ""):
            try:
                obs.append((d, float(v)))
            except ValueError:
                continue
    obs.reverse()
    return obs[:limit]


def fetch_fred() -> list[dict] | None:
    """回傳 [{'name','value','date','note'}] 或 None"""
    api_key = os.environ.get("FRED_API_KEY")
    out = []
    for sid, (name, yoy) in SERIES.items():
        try:
            obs = _api_observations(sid, api_key) if api_key else _csv_observations(sid)
            if not obs:
                continue
            date_, latest = obs[0]
            if yoy and len(obs) >= 13:
                year_ago = obs[12][1]
                val = round((latest - year_ago) / year_ago * 100, 1)
                out.append({"name": name, "value": f"{val}%", "date": date_, "note": "年增"})
            else:
                suffix = "%" if not yoy else ""
                out.append({"name": name, "value": f"{latest}{suffix}", "date": date_, "note": ""})
        except Exception:
            continue

    if out:
        return out

    # 回退:本地手動檔
    if os.path.exists(MANUAL_FILE):
        try:
            with open(MANUAL_FILE, encoding="utf-8") as f:
                d = json.load(f)
            return d.get("items", [])
        except Exception:
            pass
    return None


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    r = fetch_fred()
    for x in (r or []):
        print(f"  {x['name']}: {x['value']}  ({x.get('date','')})")
    if not r:
        print("  (總經數據暫缺)")
