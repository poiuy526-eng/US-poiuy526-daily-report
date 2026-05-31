"""手機友善 HTML 報告 builder — 產出響應式郵件版型"""
from datetime import date


# ── 小工具 ──────────────────────────────────────────────
def _c(chg):
    """漲跌顏色"""
    if chg is None:
        return "#64748b"
    return "#16a34a" if chg >= 0 else "#dc2626"


def _arrow(chg):
    if chg is None:
        return "N/A"
    return f"▲{abs(chg):.2f}%" if chg >= 0 else f"▼{abs(chg):.2f}%"


def _dot(chg):
    if chg is None:
        return "⚪"
    return "🟢" if chg > 0 else ("🔴" if chg < 0 else "⚪")


def _price(c):
    return f"${c:,.2f}" if c is not None else "N/A"


def _num(c):
    return f"{c:,.2f}" if c is not None else "N/A"


def _row(cells, bg=False):
    bgc = "#f8fafc" if bg else "#ffffff"
    tds = "".join(cells)
    return f'<tr style="background:{bgc}">{tds}</tr>'


def _td(txt, align="left", color="#1f2937", weight="400"):
    return (f'<td style="padding:7px 6px;text-align:{align};'
            f'color:{color};font-weight:{weight}">{txt}</td>')


def _section_title(num_name, color="#2563eb"):
    return (f'<div style="font-size:16px;font-weight:700;color:#0f172a;'
            f'border-left:4px solid {color};padding-left:8px;margin-bottom:10px">'
            f'{num_name}</div>')


def _summary(text):
    return (f'<div style="background:#f1f5f9;border-radius:8px;padding:10px;'
            f'margin-top:8px;font-size:13px;color:#334155;line-height:1.6">'
            f'<b>📋 總結：</b>{text}</div>')


# ── 主組裝 ──────────────────────────────────────────────
def build_mobile_html(
    report_date: date,
    indices: list[dict],
    sectors: list[dict],
    thematics: list[dict],
    holdings: list[dict],
    watchlist_data: list[dict],
    bottleneck: dict,
    fg: dict | None,
    naaim: dict | None,
    aaii: dict | None,
    news: dict,
    earnings: list[dict],
    is_sunday: bool = False,
) -> str:
    ver = "週日深度版" if is_sunday else "平日版"
    P = []
    P.append(f'''<!DOCTYPE html><html lang="zh-Hant"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>美股日報 {report_date}</title></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang TC','Microsoft JhengHei',sans-serif;-webkit-text-size-adjust:100%">
<div style="max-width:480px;margin:0 auto;background:#ffffff">
<div style="background:#0f172a;color:#fff;padding:18px 16px">
  <div style="font-size:19px;font-weight:700">🇺🇸 美股日報 v14</div>
  <div style="font-size:13px;color:#94a3b8;margin-top:3px">{report_date} · {ver} · for poiuy526</div>
</div>''')

    # 找重點漲跌
    valid_h = [h for h in holdings if h.get("chg_pct") is not None]
    best = max(valid_h, key=lambda x: x["chg_pct"]) if valid_h else None
    worst = min(valid_h, key=lambda x: x["chg_pct"]) if valid_h else None

    # ⓪ Brief
    spx = next((q for q in indices if q["ticker"] == "^GSPC"), None)
    brief_lines = []
    if best:
        brief_lines.append(f'📌 最強持股：<b>{best["ticker"]} {_arrow(best["chg_pct"])}</b>')
    if naaim and naaim.get("latest") is not None:
        brief_lines.append(f'📌 機構曝險 NAAIM：<b>{naaim["latest"]}</b>')
    if worst:
        brief_lines.append(f'⚠️ 最弱持股：{worst["ticker"]} {_arrow(worst["chg_pct"])}')
    P.append(f'''<div style="padding:16px"><div style="background:#eff6ff;border-radius:10px;padding:14px">
<div style="font-size:15px;font-weight:700;color:#1e40af;margin-bottom:8px">⓪ 60 秒 Brief</div>
<div style="font-size:14px;line-height:1.7;color:#1f2937">{"<br>".join(brief_lines)}</div></div></div>''')

    # ① 總體環境
    rows = []
    for i, q in enumerate(indices):
        nm = q.get("name", q["ticker"])
        rows.append(_row([_td(nm), _td(_num(q["close"]), "right"),
                          _td(_arrow(q["chg_pct"]), "right", _c(q["chg_pct"]), "600")], i % 2 == 0))
    P.append(f'''<div style="padding:0 16px 8px">{_section_title("① 總體環境")}
<table style="width:100%;border-collapse:collapse;font-size:14px">{"".join(rows)}</table>
{_summary("指數/商品收盤總覽。觀察大盤方向、VIX(風險情緒)、殖利率(成長股估值)、黃金(避險/通膨)。")}</div>''')

    # ② Sector Heatmap (SPDR + 主題, 全列, 由強到弱)
    all_sec = [s for s in (sectors + thematics) if s.get("chg_pct") is not None]
    all_sec.sort(key=lambda x: x["chg_pct"], reverse=True)
    rows = []
    for i, q in enumerate(all_sec):
        nm = q.get("name", q["ticker"])
        rows.append(_row([
            _td(f'{_dot(q["chg_pct"])} {nm}'),
            _td(q["ticker"], "left", "#64748b"),
            _td(_arrow(q["chg_pct"]), "right", _c(q["chg_pct"]), "600"),
        ], i % 2 == 0))
    up = [s for s in all_sec if s["chg_pct"] > 0]
    strongest = all_sec[0] if all_sec else None
    weakest = all_sec[-1] if all_sec else None
    sec_sum = (f"今日 {len(up)}/{len(all_sec)} 類股上漲。"
               f"最強 {strongest['name']}({_arrow(strongest['chg_pct'])})、"
               f"最弱 {weakest['name']}({_arrow(weakest['chg_pct'])})。"
               if strongest and weakest else "資料暫缺。")
    P.append(f'''<div style="padding:14px 16px 8px">{_section_title("② Sector Heatmap（完整）")}
<table style="width:100%;border-collapse:collapse;font-size:13.5px">{"".join(rows)}</table>
{_summary(sec_sum)}</div>''')

    # ③ 市場情緒
    s_rows = []
    if naaim:
        from fetchers.naaim import label_naaim
        s_rows.append(_row([_td("NAAIM 機構"), _td(str(naaim.get("latest", "N/A")), "right", "#1f2937", "600"),
                            _td(label_naaim(naaim.get("latest")), "right", "#ea580c")], True))
    else:
        s_rows.append(_row([_td("NAAIM 機構"), _td("⚠待驗證", "right"), _td("", "right")], True))
    if fg and fg.get("score") is not None:
        from fetchers.sentiment import label_fg
        s_rows.append(_row([_td("CNN F&G"), _td(str(fg["score"]), "right", "#1f2937", "600"),
                            _td(label_fg(fg["score"]), "right", "#ea580c")], False))
    else:
        s_rows.append(_row([_td("CNN F&G"), _td("⚠待驗證", "right"), _td("", "right")], False))
    if aaii:
        from fetchers.aaii import label_aaii
        s_rows.append(_row([_td("AAII 散戶"),
                            _td(f'多{aaii.get("bullish")}/空{aaii.get("bearish")}', "right", "#1f2937", "600"),
                            _td(label_aaii(aaii), "right", "#2563eb")], True))
    else:
        s_rows.append(_row([_td("AAII 散戶"), _td("⚠待驗證", "right"), _td("(JS頁,需手動)", "right", "#94a3b8")], True))
    P.append(f'''<div style="padding:14px 16px 8px">{_section_title("③ 市場情緒", "#7c3aed")}
<table style="width:100%;border-collapse:collapse;font-size:14px">{"".join(s_rows)}</table>
<div style="background:#fef9c3;border-radius:8px;padding:10px;margin-top:8px;font-size:13px;line-height:1.6;color:#713f12">
<b>🧭 整合判斷：</b>{_sentiment_read(naaim, fg, aaii)}</div></div>''')

    # ④ 新聞
    news_html = []
    for tk in ["CRWD", "NET", "DOCN"]:
        items = news.get(tk, [])
        if items:
            lis = "".join(f'<div style="margin:2px 0">• {n["title"]} <span style="color:#94a3b8;font-size:12px">{n.get("source","")}</span></div>' for n in items[:2])
            news_html.append(f'<div style="margin-bottom:8px"><b>{tk}</b>{lis}</div>')
    P.append(f'''<div style="padding:14px 16px 8px">{_section_title("④ 今日新聞")}
<div style="font-size:13.5px;line-height:1.5;color:#1f2937">{"".join(news_html) or "(資料暫缺)"}</div></div>''')

    # ⑥ 瓶頸輪動
    rows = []
    i = 0
    for node, tickers in bottleneck.items():
        for q in tickers:
            rows.append(_row([_td(node if q is tickers[0] else ""),
                              _td(q["ticker"]),
                              _td(_arrow(q["chg_pct"]), "right", _c(q["chg_pct"]), "600")], i % 2 == 0))
            i += 1
    P.append(f'''<div style="padding:14px 16px 8px">{_section_title("⑥ 瓶頸輪動")}
<table style="width:100%;border-collapse:collapse;font-size:13.5px">{"".join(rows)}</table>
{_summary("追蹤 5 大供應鏈瓶頸的資金流向。漲=資金流入該環節、跌=流出。")}</div>''')

    # ⑪ 核心持股
    rows = []
    for i, q in enumerate(holdings):
        rows.append(_row([_td(q["ticker"], "left", "#1f2937", "600"),
                          _td(_price(q["close"]), "right"),
                          _td(_arrow(q["chg_pct"]), "right", _c(q["chg_pct"]), "600")], i % 2 == 0))
    n_up = len([h for h in valid_h if h["chg_pct"] > 0])
    h_sum = (f"{n_up} 漲 {len(valid_h)-n_up} 跌。最強 {best['ticker']}、最弱 {worst['ticker']}。"
             if best and worst else "")
    P.append(f'''<div style="padding:14px 16px 8px">{_section_title("⑪ 核心持股")}
<table style="width:100%;border-collapse:collapse;font-size:14px">{"".join(rows)}</table>
{_summary(h_sum)}</div>''')

    # ⑫ 觀察池
    if watchlist_data:
        w = watchlist_data[0]
        P.append(f'''<div style="padding:14px 16px 8px">{_section_title("⑫ 十倍股觀察池")}
<div style="font-size:14px;line-height:1.7">🌟 <b>{w["ticker"]} {_price(w["close"])} {_arrow(w["chg_pct"])}</b></div></div>''')

    # ⑭ 財報雷達
    if earnings:
        elist = "  ｜  ".join(f'{e["date"].strftime("%m/%d")} <b>{e["ticker"]}</b>' for e in earnings[:10])
        P.append(f'''<div style="padding:14px 16px 8px">{_section_title("⑭ 財報雷達")}
<div style="font-size:13.5px;line-height:1.9;color:#1f2937">{elist}</div></div>''')

    # ⑯ 觀察點
    pts = []
    if best:
        pts.append(f'<b>1.</b> {best["ticker"]} 今日最強 {_arrow(best["chg_pct"])}，留意動能延續或回測。')
    if worst:
        pts.append(f'<b>2.</b> {worst["ticker"]} 今日最弱 {_arrow(worst["chg_pct"])}，確認支撐與是否止跌。')
    pts.append('<b>3.</b> 觀察市場廣度與情緒指標是否轉向極端。')
    pt_html = "".join(f'<div style="background:#fff7ed;border-radius:8px;padding:10px;margin-bottom:8px">{p}</div>' for p in pts)
    P.append(f'''<div style="padding:14px 16px 16px">{_section_title("⑯ 今日 3 觀察點", "#dc2626")}
<div style="font-size:14px;line-height:1.6">{pt_html}</div></div>''')

    # footer
    verified = "指數/持股/瓶頸/ETF(yfinance)"
    if naaim: verified += f"、NAAIM {naaim.get('latest')}"
    if fg and fg.get("score"): verified += f"、F&G {fg['score']}"
    if aaii: verified += "、AAII"
    if earnings: verified += "、財報日"
    P.append(f'''<div style="background:#f8fafc;padding:14px 16px;font-size:11.5px;color:#94a3b8;line-height:1.6">
✅ 已驗證：{verified}<br>資料源：yfinance · CNN · NAAIM · AAII · 投資有風險，僅供參考<br>
美股日報 v14 · for poiuy526</div></div></body></html>''')

    return "\n".join(P)


def _sentiment_read(naaim, fg, aaii) -> str:
    n = naaim.get("latest") if naaim else None
    f = fg.get("score") if fg else None
    parts = []
    if n is not None:
        if n > 100:
            parts.append("機構已過熱(>100)")
        elif n >= 80:
            parts.append(f"機構偏熱({n})")
        elif n < 30:
            parts.append(f"機構過冷({n})")
        else:
            parts.append(f"機構中性({n})")
    if f is not None:
        if f >= 80:
            parts.append("F&G 極度貪婪")
        elif f >= 55:
            parts.append("F&G 貪婪")
        elif f <= 20:
            parts.append("F&G 極度恐慌")
        elif f <= 45:
            parts.append("F&G 恐慌")
        else:
            parts.append("F&G 中性")
    if aaii and aaii.get("bearish") is not None and aaii.get("bullish") is not None:
        parts.append("散戶偏空" if aaii["bearish"] > aaii["bullish"] else "散戶偏多")
    if not parts:
        return "三指標暫缺,待驗證。"
    base = "、".join(parts) + "。"
    # 簡單情境判斷
    if n is not None and f is not None:
        if n > 100 and f >= 80:
            base += " → 頂部警訊,宜降 beta、加防禦。"
        elif n >= 80 and f >= 55:
            base += " → 偏熱但未極端,追高風險升,順勢分批、保留現金。"
        elif n < 30 and f <= 20:
            base += " → 底部買訊,可分批進場。"
        else:
            base += " → 中性偏多,維持部位。"
    return base
