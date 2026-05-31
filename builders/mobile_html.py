"""手機友善 HTML 報告 builder — 完整版響應式郵件版型"""
import os
import json
from datetime import date


# ── 小工具 ──────────────────────────────────────────────
def _c(chg):
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
    return f'<tr style="background:{bgc}">{"".join(cells)}</tr>'


def _td(txt, align="left", color="#1f2937", weight="400"):
    return (f'<td style="padding:7px 6px;text-align:{align};'
            f'color:{color};font-weight:{weight}">{txt}</td>')


def _title(num_name, color="#2563eb"):
    return (f'<div style="font-size:16px;font-weight:700;color:#0f172a;'
            f'border-left:4px solid {color};padding-left:8px;margin-bottom:10px">{num_name}</div>')


def _summary(text):
    return (f'<div style="background:#f1f5f9;border-radius:8px;padding:10px;'
            f'margin-top:8px;font-size:13px;color:#334155;line-height:1.6">'
            f'<b>📋 總結：</b>{text}</div>')


def _box(text, bg, border, fg):
    return (f'<div style="background:{bg};border-radius:8px;padding:10px;'
            f'margin-bottom:8px;font-size:13.5px;line-height:1.6;color:{fg}">{text}</div>')


def _load_json(fname):
    here = os.path.dirname(os.path.dirname(__file__))
    p = os.path.join(here, fname)
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def _find(lst, ticker):
    return next((q for q in lst if q.get("ticker") == ticker), None)


# ── 產業學堂輪換池(週日)──────────────────────────────
ACADEMY = {
    "robot": ("機器人供應鏈五層 — 利潤怎麼分？",
              "利潤分布（毛利高→低）：<br>"
              "⑤ 軟體+AI大腦 60-80% → NVDA、GOOGL<br>"
              "④ 感知系統 35-50% → AMBA、MBLY<br>"
              "③ <b>動力系統 30-45%（核心）</b> → 諧波減速器 Harmonic(6324.JP, 60%市佔)、Yaskawa<br>"
              "① 上游原料 15-30% → MP(稀土)、ALB(鋰)<br>"
              "⑥ OEM整機 5-25% → TSLA(Optimus)、UBTech<br>"
              "💡 <b>整機最辛苦，真正賺錢在「軟體大腦」與「諧波減速器」</b>。"
              "投資別只看整機品牌，往「賣鏟子」的零組件找。中國控零組件 70%、Pentagon 是關鍵客戶。"),
}


# ── 主組裝 ──────────────────────────────────────────────
def build_mobile_html(
    report_date, indices, sectors, thematics, holdings, watchlist_data,
    bottleneck, fg, naaim, aaii, news, earnings, market_news=None, macro=None, is_sunday=False,
):
    market_news = market_news or []
    macro = macro or []
    ver = "週日深度版" if is_sunday else "平日版"
    P = []
    P.append(f'''<!DOCTYPE html><html lang="zh-Hant"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>美股日報 {report_date}</title></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang TC','Microsoft JhengHei',sans-serif;-webkit-text-size-adjust:100%">
<div style="max-width:480px;margin:0 auto;background:#ffffff">
<div style="background:#0f172a;color:#fff;padding:18px 16px">
  <div style="font-size:19px;font-weight:700">🇺🇸 美股{"週報" if is_sunday else "日報"} v14</div>
  <div style="font-size:13px;color:#94a3b8;margin-top:3px">{report_date} · {ver} · for poiuy526</div>
</div>''')

    valid_h = [h for h in holdings if h.get("chg_pct") is not None]
    best = max(valid_h, key=lambda x: x["chg_pct"]) if valid_h else None
    worst = min(valid_h, key=lambda x: x["chg_pct"]) if valid_h else None

    # ⓪ Brief
    spx = _find(indices, "^GSPC"); ndx = _find(indices, "^IXIC"); vix = _find(indices, "^VIX")
    bl = []
    brief_idx = []
    if spx: brief_idx.append(f'S&P {_arrow(spx["chg_pct"])}')
    if ndx: brief_idx.append(f'Nasdaq {_arrow(ndx["chg_pct"])}')
    if vix: brief_idx.append(f'VIX {_num(vix["close"])}')
    if brief_idx: bl.append("📊 " + "　".join(brief_idx))
    if best: bl.append(f'🔥 最強：<b>{best["ticker"]} {_arrow(best["chg_pct"])}</b>')
    if naaim and naaim.get("latest") is not None:
        bl.append(f'🏛 機構 NAAIM <b>{naaim["latest"]}</b>' +
                  (f'｜F&G {fg["score"]}' if fg and fg.get("score") else ''))
    if worst: bl.append(f'⚠️ 最弱：{worst["ticker"]} {_arrow(worst["chg_pct"])}')
    P.append(f'''<div style="padding:16px"><div style="background:#eff6ff;border-radius:10px;padding:14px">
<div style="font-size:15px;font-weight:700;color:#1e40af;margin-bottom:8px">⓪ 60 秒 Brief</div>
<div style="font-size:14px;line-height:1.8;color:#1f2937">{"<br>".join(bl)}</div></div></div>''')

    # ① 總體環境
    rows = [_row([_td(q.get("name", q["ticker"])), _td(_num(q["close"]), "right"),
                  _td(_arrow(q["chg_pct"]), "right", _c(q["chg_pct"]), "600")], i % 2 == 0)
            for i, q in enumerate(indices)]
    macro_sum = "大盤方向 + 風險情緒(VIX) + 殖利率(估值) + 黃金(避險)。"
    if vix and vix.get("chg_pct") is not None:
        macro_sum += f' VIX {"下降→風險偏好升" if vix["chg_pct"] < 0 else "上升→避險升溫"}。'
    # 總經數據區塊(FRED)
    macro_html = ""
    macro_items = [m for m in macro if isinstance(m, dict) and m.get("name")]
    if macro_items:
        chips = "".join(
            f'<span style="display:inline-block;background:#fff7ed;border:1px solid #fed7aa;'
            f'border-radius:6px;padding:3px 8px;margin:3px 3px 0 0;font-size:12.5px;color:#9a3412">'
            f'{m["name"]} <b>{m["value"]}</b>{("・"+m["note"]) if m.get("note") else ""}</span>'
            for m in macro_items)
        macro_html = (f'<div style="margin-top:8px"><div style="font-size:12.5px;color:#64748b;margin-bottom:2px">'
                      f'📈 總經數據(FRED)</div>{chips}</div>')
    P.append(f'''<div style="padding:0 16px 8px">{_title("① 總體環境")}
<table style="width:100%;border-collapse:collapse;font-size:14px">{"".join(rows)}</table>
{macro_html}{_summary(macro_sum)}</div>''')

    # ② Sector Heatmap(只顯示最強5+最弱5,共10檔)
    all_sec = [s for s in (sectors + thematics) if s.get("chg_pct") is not None]
    all_sec.sort(key=lambda x: x["chg_pct"], reverse=True)
    nup = len([s for s in all_sec if s["chg_pct"] > 0])
    ndn = len([s for s in all_sec if s["chg_pct"] < 0])
    # 取頭5尾5(去重)
    if len(all_sec) > 10:
        shown_sec = all_sec[:5] + all_sec[-5:]
    else:
        shown_sec = all_sec
    rows = []
    for i, q in enumerate(shown_sec):
        # 頭尾之間插分隔
        if len(all_sec) > 10 and i == 5:
            rows.append('<tr><td colspan="3" style="padding:3px 6px;text-align:center;color:#cbd5e1;font-size:11px">··· 中段 '
                        f'{len(all_sec)-10} 檔略 ···</td></tr>')
        rows.append(_row([_td(f'{_dot(q["chg_pct"])} {q.get("name", q["ticker"])}'),
                          _td(q["ticker"], "left", "#64748b"),
                          _td(_arrow(q["chg_pct"]), "right", _c(q["chg_pct"]), "600")], i % 2 == 0))
    # 豐富總結
    if all_sec:
        st, wk = all_sec[0], all_sec[-1]
        breadth = ("廣度極窄(資金高度集中單一主題),為中期背離警訊" if nup <= len(all_sec) // 3
                   else "廣度健康(普漲)" if nup >= len(all_sec) * 2 // 3
                   else "廣度中性(漲跌互見)")
        # 領漲/落後主題群(取前3、後3)
        top3 = "、".join(f'{s.get("name")}({_arrow(s["chg_pct"])})' for s in all_sec[:3])
        bot3 = "、".join(f'{s.get("name")}({_arrow(s["chg_pct"])})' for s in all_sec[-3:])
        spread = st["chg_pct"] - wk["chg_pct"]
        sec_sum = (f"全 {len(all_sec)} 檔中 <b>{nup} 漲 / {ndn} 跌</b>，{breadth}。<br>"
                   f"🔼 領漲：{top3}<br>🔽 落後：{bot3}<br>"
                   f"強弱差 {spread:.2f} 個百分點 — "
                   f"{'資金分歧大、明顯主題輪動' if spread > 5 else '類股同向、系統性行情'}。")
    else:
        sec_sum = "資料暫缺。"
    P.append(f'''<div style="padding:14px 16px 8px">{_title("② Sector Heatmap")}
<div style="font-size:11.5px;color:#94a3b8;margin-bottom:8px">顯示最強 5 + 最弱 5（共 {len(all_sec)} 檔追蹤）</div>
<table style="width:100%;border-collapse:collapse;font-size:13.5px">{"".join(rows)}</table>{_summary(sec_sum)}</div>''')

    # ③ 市場情緒
    s_rows = []
    from fetchers.naaim import label_naaim
    from fetchers.sentiment import label_fg
    from fetchers.aaii import label_aaii
    if naaim:
        s_rows.append(_row([_td("NAAIM 機構"), _td(str(naaim.get("latest", "N/A")), "right", "#1f2937", "600"),
                            _td(label_naaim(naaim.get("latest")), "right", "#ea580c")], True))
    else:
        s_rows.append(_row([_td("NAAIM 機構"), _td("⚠待驗證", "right"), _td("", "right")], True))
    if fg and fg.get("score") is not None:
        s_rows.append(_row([_td("CNN F&G"), _td(str(fg["score"]), "right", "#1f2937", "600"),
                            _td(label_fg(fg["score"]), "right", "#ea580c")], False))
    else:
        s_rows.append(_row([_td("CNN F&G"), _td("⚠待驗證", "right"), _td("", "right")], False))
    if aaii:
        s_rows.append(_row([_td("AAII 散戶"),
                            _td(f'多{aaii.get("bullish")}/空{aaii.get("bearish")}', "right", "#1f2937", "600"),
                            _td(label_aaii(aaii), "right", "#2563eb")], True))
    else:
        s_rows.append(_row([_td("AAII 散戶"), _td("⚠待驗證", "right"), _td("(JS頁,需手動)", "right", "#94a3b8")], True))
    P.append(f'''<div style="padding:14px 16px 8px">{_title("③ 市場情緒（三指標）", "#7c3aed")}
<table style="width:100%;border-collapse:collapse;font-size:14px">{"".join(s_rows)}</table>
{_box("<b>🧭 整合判斷：</b>" + _sentiment_read(naaim, fg, aaii), "#fef9c3", "", "#713f12")}</div>''')

    # ④ 今日新聞快報(大盤重大事件 + 持股個股焦點,豐富版)
    def _newslink(n):
        t = n.get("title_zh") or n["title"]  # 優先用中文
        src = n.get("source", "")
        if n.get("url"):
            t = f'<a href="{n["url"]}" style="color:inherit;text-decoration:none">{t}</a>'
        return f'{t} <span style="color:#94a3b8;font-size:11.5px">{src}</span>'

    nh = []
    # 🔥 重大事件(大盤/總經新聞,色塊)。個股新聞已併入 ⑪ 核心持股,此處不重複。
    if market_news:
        for n in market_news[:7]:
            nh.append(_box(f'📰 {_newslink(n)}', "#fef9f5", "", "#7c2d12"))
    else:
        nh.append('<div style="color:#94a3b8;font-size:13px">(大盤新聞暫缺)</div>')
    P.append(f'''<div style="padding:14px 16px 8px">{_title("④ 今日新聞快報 · 大盤重大事件")}
<div style="font-size:11.5px;color:#94a3b8;margin-bottom:6px">個股新聞請見 ⑪ 核心持股</div>{"".join(nh)}</div>''')

    # ⑥ 瓶頸輪動(每環節一張卡 + 議價力/結構訊號/觀察)
    from knowledge import BOTTLENECK_KB
    cards = []
    inflow, outflow = [], []
    for node, ts in bottleneck.items():
        kb = BOTTLENECK_KB.get(node, {})
        quotes = "　".join(f'{q["ticker"]} <span style="color:{_c(q["chg_pct"])};font-weight:600">{_arrow(q["chg_pct"])}</span>' for q in ts)
        lead = ts[0].get("chg_pct")
        if lead is not None:
            (inflow if lead > 0 else outflow).append(node)
        flow = "📈 流入" if (lead is not None and lead > 0) else ("📉 流出" if lead is not None else "—")
        cards.append(
            f'<div style="border:1px solid #e5e7eb;border-radius:8px;padding:10px;margin-bottom:8px">'
            f'<div style="font-weight:700;font-size:13.5px;color:#0f172a">{node} <span style="color:#ea580c">{kb.get("熱度","")}</span> '
            f'<span style="float:right;font-size:12px">{flow}</span></div>'
            f'<div style="font-size:13px;margin:4px 0">{quotes}</div>'
            f'<div style="font-size:12.5px;color:#475569;line-height:1.6">'
            f'議價力：{kb.get("議價力","—")}<br>'
            f'訊號：{kb.get("結構訊號","—")}<br>'
            f'👀 觀察：{kb.get("觀察","—")}</div></div>'
        )
    bn_sum = "資金流向：" + ("📈 " + "、".join(inflow) if inflow else "") + ("　📉 " + "、".join(outflow) if outflow else "")
    P.append(f'''<div style="padding:14px 16px 8px">{_title("⑥ 瓶頸輪動（5 環節）")}
{"".join(cards)}{_summary(bn_sum)}</div>''')

    # ⑦ 產業聚焦(多主題比較 + 重點分析)
    from knowledge import THEME_GROUPS
    # 匯總當日所有可得漲跌
    pool = {}
    for q in (holdings + watchlist_data + sectors + thematics + sum(bottleneck.values(), [])):
        if q.get("chg_pct") is not None and q["ticker"] not in pool:
            pool[q["ticker"]] = q["chg_pct"]
    # 算各主題平均
    theme_stats = []
    for theme, tks in THEME_GROUPS.items():
        vals = [(tk, pool[tk]) for tk in tks if tk in pool]
        if vals:
            avg = sum(v for _, v in vals) / len(vals)
            theme_stats.append({"theme": theme, "avg": avg, "members": vals})
    theme_stats.sort(key=lambda x: x["avg"], reverse=True)

    cards = []
    for ts in theme_stats:
        dot = _dot(ts["avg"])
        members = "　".join(
            f'{tk} <span style="color:{_c(v)};font-weight:600">{_arrow(v)}</span>' for tk, v in ts["members"]
        )
        cards.append(
            f'<div style="padding:8px 0;border-bottom:1px solid #f1f5f9">'
            f'<div style="font-weight:700;font-size:13.5px">{dot} {ts["theme"]} '
            f'<span style="float:right;color:{_c(ts["avg"])}">{_arrow(ts["avg"])}</span></div>'
            f'<div style="font-size:12.5px;color:#475569;margin-top:2px">{members}</div></div>'
        )

    # 重點分析(資料驅動:領漲 vs 落後主題)
    focus_an = ""
    if theme_stats:
        lead = theme_stats[0]
        lag = theme_stats[-1]
        focus_an = (f'今日 <b>{lead["theme"]}</b> 領漲(均 {_arrow(lead["avg"])})、'
                    f'<b>{lag["theme"]}</b> 最弱(均 {_arrow(lag["avg"])})。')
        # 軟體 vs 半導體輪動觀察
        soft = next((t for t in theme_stats if t["theme"] == "AI 軟體"), None)
        semi = next((t for t in theme_stats if t["theme"] == "半導體/記憶體"), None)
        if soft and semi:
            if soft["avg"] > semi["avg"] + 1:
                focus_an += " AI 資金<b>由半導體輪向軟體</b>(軟體強過半導體)。"
            elif semi["avg"] > soft["avg"] + 1:
                focus_an += " AI 資金<b>偏硬體/半導體</b>(半導體強過軟體)。"
            else:
                focus_an += " AI 軟硬體同步,題材全面。"
    P.append(f'''<div style="padding:14px 16px 8px">{_title("⑦ 產業聚焦（主題比較）")}
<div style="font-size:11.5px;color:#94a3b8;margin-bottom:6px">各主題=代表個股當日平均，由強到弱</div>
{"".join(cards)}
<div style="background:#eef2ff;border-radius:8px;padding:11px;margin-top:10px;font-size:13px;color:#3730a3;line-height:1.6">
<b>🔍 重點分析：</b>{focus_an}</div></div>''')

    # ⑧ 廣域產業雷達(結構主題)
    rklb = _find(watchlist_data, "RKLB")
    rklb_px = f'（{_arrow(rklb["chg_pct"])}）' if rklb and rklb.get("chg_pct") is not None else ''
    radar = (
        f'🚀 <b>太空/國防</b>（本週主題）<br>'
        f'RKLB{rklb_px} Neutron H2 2026 首飛｜SpaceX IPO 題材｜ASTS 衛星｜LMT/NOC/RTX 國防主線<br><br>'
        f'🤖 <b>機器人/Physical AI</b>（下一輪）<br>'
        f'TSLA Optimus 量產｜NVDA Isaac/GR00T 模擬平台｜諧波減速器(6324.JP)｜詳見 ⑨ 學堂<br><br>'
        f'🥇 <b>貴金屬</b>：黃金避險+通膨對沖需求延續　⚡ <b>核電/SMR</b>：CEG/OKLO/SMR'
    )
    P.append(f'''<div style="padding:14px 16px 8px">{_title("⑧ 廣域產業雷達")}
<div style="font-size:13px;line-height:1.7;color:#1f2937">{radar}</div></div>''')

    # ⑨ 產業學堂(週日)
    if is_sunday:
        t, body = ACADEMY["robot"]
        P.append(f'''<div style="padding:14px 16px 8px">{_title("⑨ 產業學堂", "#0d9488")}
<div style="font-size:14px;font-weight:600;color:#0f766e;margin-bottom:6px">{t}</div>
<div style="font-size:13.5px;line-height:1.75;color:#1f2937">{body}</div></div>''')

    # ⑩ 低點布局(週日):持股跌逾 3%
    if is_sunday:
        dips = [h for h in valid_h if h["chg_pct"] < -3]
        if dips:
            db = "".join(f'🌟 <b>{d["ticker"]} {_price(d["close"])}</b>（{_arrow(d["chg_pct"])}）：'
                         f'急跌但題材未必壞，觀察支撐帶；跌破改保守。<br>' for d in dips)
        else:
            db = "本週無持股急跌逾 3%，暫無低點布局候選。"
        P.append(f'''<div style="padding:14px 16px 8px">{_title("⑩ 低點布局（觀察非建議）", "#0d9488")}
{_box(db, "#f0fdfa", "", "#134e4a")}</div>''')

    # ⑪ 核心持股(代號/價/漲跌 + 重點分析:方向+定位+催化劑+當日新聞)
    from knowledge import HOLDINGS_KB
    def _dir_word(chg):
        if chg is None:
            return "—"
        if chg >= 3:
            return "▲ 強漲"
        if chg > 0:
            return "▲ 上漲"
        if chg <= -3:
            return "▼ 重挫"
        if chg < 0:
            return "▼ 回落"
        return "⚪ 持平"
    cards = []
    for q in holdings:
        kb = HOLDINGS_KB.get(q["ticker"], {})
        pos = kb.get("定位", "")
        cat = kb.get("催化劑", "")
        # 當日新聞(中文)一句話
        ni = news.get(q["ticker"], [])
        news_zh = (ni[0].get("title_zh") or ni[0].get("title", "")) if ni else ""
        news_line = f'<div style="font-size:12px;color:#475569;margin-top:3px">📰 {news_zh}</div>' if news_zh else ""
        cards.append(
            f'<div style="padding:9px 0;border-bottom:1px solid #f1f5f9">'
            f'<div><b style="font-size:14px">{q["ticker"]}</b> '
            f'<span style="color:#475569">{_price(q["close"])}</span> '
            f'<span style="color:{_c(q["chg_pct"])};font-weight:700;float:right">'
            f'{_dir_word(q["chg_pct"])} {_arrow(q["chg_pct"])}</span></div>'
            f'<div style="font-size:12px;color:#64748b;margin-top:3px">'
            f'<b>{pos}</b>{("　🎯 " + cat) if cat else ""}</div>'
            f'{news_line}</div>'
        )
    nu = len([h for h in valid_h if h["chg_pct"] > 0])
    # 重點分析(資料驅動)
    def _pos(h): return (h.get("chg_pct") or 0) > 0
    def _neg(h): return (h.get("chg_pct") or 0) < 0
    soft = [h["ticker"] for h in holdings if h["ticker"] in ("CRWD", "NET", "DOCN") and _pos(h)]
    hard = [h["ticker"] for h in holdings if h["ticker"] in ("TSM", "COHR", "SMH") and _neg(h)]
    analysis = (f"{nu} 漲 {len(valid_h)-nu} 跌。最強 <b>{best['ticker']}</b>({_arrow(best['chg_pct'])})、"
                f"最弱 <b>{worst['ticker']}</b>({_arrow(worst['chg_pct'])})。" if best and worst else "")
    if soft and hard:
        analysis += f" 軟體({'/'.join(soft)})強、硬體({'/'.join(hard)})弱 → 組合內資金<b>由硬體輪向軟體</b>。"
    elif soft:
        analysis += f" 軟體({'/'.join(soft)})領漲,AI 軟體題材延續。"
    P.append(f'''<div style="padding:14px 16px 8px">{_title("⑪ 核心持股快照")}
<div style="font-size:14px">{"".join(cards)}</div>
<div style="background:#eef2ff;border-radius:8px;padding:11px;margin-top:10px;font-size:13px;color:#3730a3;line-height:1.6">
<b>🔍 重點分析：</b>{analysis}</div></div>''')

    # ⑫ 十倍股觀察池(完整卡片:十倍邏輯/觀察/風險)
    from knowledge import TENBAGGER_POOL
    def _tenbagger_card(ticker, quote=None, star="🌟"):
        kb = TENBAGGER_POOL.get(ticker)
        if not kb:
            return ""
        px = ""
        if quote and quote.get("close") is not None:
            px = f' <span style="color:{_c(quote.get("chg_pct"))};font-weight:600">{_price(quote["close"])} {_arrow(quote.get("chg_pct"))}</span>'
        logic = "".join(f'<li>{x}</li>' for x in kb.get("十倍邏輯", []))
        return (
            f'<div style="border:1px solid #e5e7eb;border-radius:8px;padding:10px;margin-bottom:8px">'
            f'<div style="font-weight:700;color:#0f172a">{star} {ticker} · {kb["名稱"]}{px}'
            f'<span style="float:right;font-size:11px;color:#94a3b8">{kb.get("市值","")}</span></div>'
            f'<div style="font-size:12.5px;color:#334155;line-height:1.6;margin-top:4px">'
            f'<b>十倍邏輯：</b><ul style="margin:2px 0 4px 18px;padding:0">{logic}</ul>'
            f'<b>優勢：</b>{kb.get("競爭優勢","—")}<br>'
            f'👀 <b>觀察：</b>{kb.get("觀察","—")}<br>'
            f'⚠️ <b>風險：</b>{kb.get("風險","—")}</div></div>'
        )
    cards = []
    # 組合內觀察池(RKLB)
    if watchlist_data:
        w = watchlist_data[0]
        cards.append(_tenbagger_card(w["ticker"], w, "⭐"))
    # 組合外輪換(依星期幾輪 GEV/OKLO)
    pool_ext = ["GEV", "OKLO"]
    pick = pool_ext[report_date.toordinal() % len(pool_ext)]
    cards.append(_tenbagger_card(pick, None, "🌟"))
    P.append(f'''<div style="padding:14px 16px 8px">{_title("⑫ 十倍股觀察池")}
{"".join(c for c in cards if c)}</div>''')

    # ⑬ 操盤指令
    orders = []
    if best:
        orders.append(_row([_td("★★★★ 重點"), _td(f'{best["ticker"]} 持有，強勢但留意財報前勿追高')], True))
    if watchlist_data:
        orders.append(_row([_td("🌟 觀察池"), _td(f'{watchlist_data[0]["ticker"]} 回支撐區留意')], False))
    if worst:
        orders.append(_row([_td("⚠️ 警示"), _td(f'{worst["ticker"]} 確認支撐，跌破設停損')], True))
    P.append(f'''<div style="padding:14px 16px 8px">{_title("⑬ 操盤指令")}
<table style="width:100%;border-collapse:collapse;font-size:13.5px">{"".join(orders)}</table></div>''')

    # ⑭ 財報雷達 + 經濟數據
    er = ""
    if earnings:
        er = "  ｜  ".join(f'{e["date"].strftime("%m/%d")} <b>{e["ticker"]}</b>' for e in earnings[:10])
    cal = _load_json("manual_calendar.json")
    cal_html = ""
    if cal and cal.get("events"):
        evs = "　".join(f'{e["date"]} {e["name"]}' for e in cal["events"])
        cal_html = _box(f'📅 <b>本週經濟數據：</b><br>{evs}', "#fff7ed", "", "#9a3412")
    P.append(f'''<div style="padding:14px 16px 8px">{_title("⑭ 財報雷達 + 經濟數據")}
<div style="font-size:13.5px;line-height:1.9;color:#1f2937">{er or "(財報日暫缺)"}</div>{cal_html}</div>''')

    # ⑮ 亞太接棒
    tsm = _find(holdings, "TSM")
    asia = "🇹🇼 台股：留意台積電 2330 對應 TSM ADR"
    if tsm and tsm.get("chg_pct") is not None:
        asia += f'（{_arrow(tsm["chg_pct"])}）'
    asia += "；旺矽(6223)/京元電(2449) 隨記憶體連動<br>🇯🇵 半導體設備 Tokyo Electron/Disco/Lasertec<br>💱 台幣關注 28.7 區間"
    P.append(f'''<div style="padding:14px 16px 8px">{_title("⑮ 亞太接棒")}
<div style="font-size:13.5px;line-height:1.7;color:#1f2937">{asia}</div></div>''')

    # ⑯ 觀察點 + 策略
    pts = []
    if best:
        pts.append(f'<b>1. {best["ticker"]}</b> 今日最強 {_arrow(best["chg_pct"])}，留意動能延續或利多出盡回測。')
    if worst:
        pts.append(f'<b>2. {worst["ticker"]}</b> 今日最弱 {_arrow(worst["chg_pct"])}，確認支撐與止跌訊號。')
    pts.append('<b>3.</b> 觀察情緒指標(NAAIM/F&G)是否轉向極端、市場廣度是否擴散。')
    ph = "".join(_box(p, "#fff7ed", "", "#1f2937") for p in pts)
    strat = (f'💡 <b>整體策略</b><br>持有：強勢核心({best["ticker"] if best else "—"})<br>'
             f'謹慎：追高、情緒過熱下的 beta<br>對沖：黃金(GLD)<br>'
             f'下個轉折：見財報雷達 + 情緒是否破極端')
    P.append(f'''<div style="padding:14px 16px 16px">{_title("⑯ 今日 3 觀察點", "#dc2626")}
<div style="font-size:14px;line-height:1.6">{ph}</div>
<div style="background:#0f172a;color:#e2e8f0;border-radius:8px;padding:12px;margin-top:12px;font-size:13.5px;line-height:1.7">{strat}</div></div>''')

    # footer
    v = "指數/持股/瓶頸/ETF(yfinance)"
    if naaim: v += f"、NAAIM {naaim.get('latest')}"
    if fg and fg.get("score"): v += f"、F&G {fg['score']}"
    if aaii: v += "、AAII"
    if earnings: v += "、財報日"
    P.append(f'''<div style="background:#f8fafc;padding:14px 16px;font-size:11.5px;color:#94a3b8;line-height:1.6">
✅ 已驗證：{v}<br>資料源：yfinance · CNN · NAAIM · AAII · tradingeconomics · 投資有風險，僅供參考<br>
美股{"週報" if is_sunday else "日報"} v14 · for poiuy526</div></div></body></html>''')

    return "\n".join(P)


def _sentiment_read(naaim, fg, aaii):
    n = naaim.get("latest") if naaim else None
    f = fg.get("score") if fg else None
    parts = []
    if n is not None:
        parts.append("機構已過熱(>100)" if n > 100 else f"機構偏熱({n})" if n >= 80
                     else f"機構過冷({n})" if n < 30 else f"機構中性({n})")
    if f is not None:
        parts.append("F&G 極度貪婪" if f >= 80 else "F&G 貪婪" if f >= 55
                     else "F&G 極度恐慌" if f <= 20 else "F&G 恐慌" if f <= 45 else "F&G 中性")
    if aaii and aaii.get("bearish") is not None and aaii.get("bullish") is not None:
        parts.append("散戶偏空" if aaii["bearish"] > aaii["bullish"] else "散戶偏多")
    if not parts:
        return "三指標暫缺,待驗證。"
    base = "、".join(parts) + "。"
    if n is not None and f is not None:
        if n > 100 and f >= 80:
            base += " → 頂部警訊,宜降 beta、加防禦。"
        elif n >= 80 and f >= 55:
            base += " → 偏熱但未極端,追高風險升,順勢分批、保留現金。"
        elif n < 30 and f <= 20:
            base += " → 底部買訊,可分批進場。"
        else:
            base += " → 中性偏多,維持部位。"
    if aaii and n is not None and aaii.get("bearish") and aaii.get("bullish"):
        if n >= 80 and aaii["bearish"] > aaii["bullish"]:
            base += " 機構樂觀但散戶偏空 → 健康分歧(憂慮之牆),非立即頂部。"
    return base
