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


def _theme_avg(tickers, pool):
    vals = [pool[t] for t in tickers if t in pool]
    return (sum(vals) / len(vals)) if vals else None


def _pick_debate(holdings, watchlist_data, sectors, thematics, bottleneck,
                 debate_pool, stock_debate):
    """依當日資料自動選辯題,回傳 (debate_dict, data_line)。
    優先序:大幅波動個股(±8%, 有專屬辯題) > 軟硬體輪動分歧 > AI capex(預設)。"""
    # 當日漲跌池
    pool = {}
    for q in (holdings + watchlist_data + sectors + thematics + sum(bottleneck.values(), [])):
        if q.get("chg_pct") is not None and q["ticker"] not in pool:
            pool[q["ticker"]] = q["chg_pct"]

    # 1) 大幅波動個股(優先觸發專屬辯題)
    big = [(t, c) for t, c in pool.items() if t in stock_debate and abs(c) >= 8]
    if big:
        big.sort(key=lambda x: abs(x[1]), reverse=True)
        t, c = big[0]
        return stock_debate[t], f'{t} {_arrow(c)}(單日波動逾 8%,觸發專屬辯題)'

    # 2) 軟硬體輪動分歧
    soft = _theme_avg(["IGV", "CRWD", "NET", "DOCN"], pool)
    semi = _theme_avg(["SMH", "SOXX", "TSM", "MU", "DRAM"], pool)
    if soft is not None and semi is not None and abs(soft - semi) >= 1.5:
        dl = f'AI 軟體均 {_arrow(soft)} vs 半導體均 {_arrow(semi)}(差 {abs(soft-semi):.2f}pp)'
        return debate_pool["software_rotation"], dl

    # 3) 太空股顯著走弱
    space = _theme_avg(["RKLB", "NASA", "ITA"], pool)
    if space is not None and space <= -4:
        return debate_pool["space_ipo"], f'太空/國防均 {_arrow(space)}'

    # 4) 預設:AI capex 永續辯論
    return debate_pool["ai_capex"], None


def _chg_pool(*lists):
    pool = {}
    for lst in lists:
        for q in lst:
            if q.get("chg_pct") is not None and q["ticker"] not in pool:
                pool[q["ticker"]] = q["chg_pct"]
    return pool


def _dirw(chg, up="走強", flat="持平", down="回落"):
    if chg is None:
        return flat
    return up if chg > 0 else (down if chg < 0 else flat)


def _heat_top5(holdings, watchlist_data, thematics):
    """🔥 熱度 Top5:依 |當日漲跌| 取前 5,給 🔥 數量與訊號文字。"""
    seen, items = set(), []
    for q in (holdings + watchlist_data + thematics):
        t, c = q.get("ticker"), q.get("chg_pct")
        if t and c is not None and t not in seen:
            seen.add(t); items.append((t, c))
    items.sort(key=lambda x: abs(x[1]), reverse=True)
    out = []
    for t, c in items[:5]:
        a = abs(c)
        fire = "🔥🔥🔥🔥🔥" if a >= 8 else "🔥🔥🔥🔥" if a >= 5 else "🔥🔥🔥" if a >= 3 else "🔥🔥" if a >= 1.5 else "🔥"
        if c >= 5:
            sig = "強漲,追價熱"
        elif c > 0:
            sig = "上漲,留意延續"
        elif c <= -8:
            sig = "重挫,恐慌賣壓"
        elif c <= -3:
            sig = "下跌,留意支撐"
        else:
            sig = "回落"
        out.append((t, c, fire, sig))
    return out


def _asia_handoff(holdings, watchlist_data, sectors, thematics, bottleneck, indices):
    """§⑮ 亞太接棒:分 台/日/中/匯,依當日實際數據條件式生成。"""
    pool = _chg_pool(holdings, watchlist_data, sectors, thematics, sum(bottleneck.values(), []))
    tsm = _find(holdings, "TSM")
    tsm_c = tsm.get("chg_pct") if tsm else None
    mem = _theme_avg(["MU", "DRAM"], pool)
    soft = _theme_avg(["IGV", "CRWD", "NET", "DOCN"], pool)
    soxx = pool.get("SOXX")
    crcl = _find(holdings, "CRCL")
    crcl_c = crcl.get("chg_pct") if crcl else None
    gold = _find(indices, "GC=F")
    usd = _find(indices, "DX-Y.NYB")
    tnx = _find(indices, "^TNX")
    wti = _find(indices, "CL=F")

    # 🇹🇼 台股
    tw = [f'TSM ADR {_arrow(tsm_c) if tsm_c is not None else ""} → 台積電 2330 今日預計同步{_dirw(tsm_c)}']
    if mem is not None:
        if mem > 0:
            mu = pool.get("MU"); dr = pool.get("DRAM")
            tag = "、".join(x for x in [f'MU {_arrow(mu)}' if mu is not None else "", f'DRAM {_arrow(dr)}' if dr is not None else ""] if x)
            tw.append(f'記憶體走強({tag})→ 封測旺矽(6223)、京元電(2449) 受惠')
        else:
            tw.append('記憶體回落,封測旺矽(6223)/京元電(2449) 留意跟跌')
    if (soft is not None and soft <= -2) or (soxx is not None and soxx < 0):
        tw.append('美股 ASIC/軟體走弱 → 世芯-KY(3661)、創意(3443) 留意情緒外溢')
    elif soxx is not None and soxx > 1:
        tw.append('費半走強 → 世芯-KY(3661)、創意(3443) 可望同步')
    gold_c = gold.get("chg_pct") if gold else None
    tw.append(f'地緣/避險{("(黃金 " + _arrow(gold_c) + ")") if gold_c is not None else ""} → 台幣關注 28.7 支撐')

    # 🇯🇵 日股
    jp = [f'半導體設備(Tokyo Electron/Disco/Lasertec)隨費半 {(_arrow(soxx)) if soxx is not None else ""} '
          f'{"偏穩" if (soxx or 0) >= 0 else "承壓"}']
    jp.append('避險情緒下日圓若走強,壓抑出口股')

    # 🇨🇳 港股
    cn = ['中概 AI(百度 9888.HK / 商湯 0020.HK)隨美股科技分化波動']
    if crcl_c is not None and crcl_c <= -3:
        cn.append(f'加密/穩定幣情緒受 CRCL {_arrow(crcl_c)} 拖累,港股相關標的留意')

    # 💱 匯市
    usd_c = usd.get("chg_pct") if usd else None
    tnx_c = tnx.get("chg_pct") if tnx else None
    usd_dir = "偏強" if (usd_c or 0) > 0 else ("偏弱" if (usd_c or 0) < 0 else "持平")
    fx = [f'美元指數 {_arrow(usd_c) if usd_c is not None else ""}{("、10Y " + _arrow(tnx_c)) if tnx_c is not None else ""} → 美元{usd_dir}']
    fx.append(f'台幣 28.7 關鍵支撐{("；黃金 " + _num(gold.get("close")) + " " + _arrow(gold_c)) if gold and gold.get("close") is not None else ""}')

    def _blk(flag, items):
        return f'<b>{flag}</b><br>' + "<br>".join("・" + i for i in items)
    return "<br><br>".join([
        _blk("🇹🇼 台股", tw), _blk("🇯🇵 日股", jp), _blk("🇨🇳 港股", cn), _blk("💱 匯市", fx)])


def _next_catalysts(earnings, cal, report_date):
    """組『下個轉折』字串:最近 2 場持股財報 + 本週經濟數據。"""
    bits = []
    if earnings:
        up = [e for e in earnings if e.get("date") and e["date"] >= report_date]
        up = up[:2] if up else earnings[:2]
        def _d(e):
            d = e.get("date")
            return f'{d.month}/{d.day}' if hasattr(d, "month") else str(d)
        if up:
            bits.append("、".join(f'{_d(e)} {e["ticker"]} 財報' for e in up))
    if cal and cal.get("events"):
        today = report_date.strftime("%m/%d") if hasattr(report_date, "strftime") else ""
        evs = [e for e in cal["events"] if e.get("date", "") >= today] or cal["events"]
        ev = evs[:2]
        bits.append("、".join(f'{e.get("date","")} {e.get("name","")}' for e in ev))
    return "；".join(b for b in bits if b) or "見 §⑭ 財報雷達"


def _observations(holdings, valid_h, best, worst, watchlist_data, sectors, thematics,
                  bottleneck, naaim, fg, indices, earnings, cal, report_date):
    """§⑯ 三觀察點(各含場景 A/B + 明日做什麼)+ 整體策略。資料驅動。"""
    pool = _chg_pool(holdings, watchlist_data, sectors, thematics, sum(bottleneck.values(), []))
    soft = _theme_avg(["IGV", "CRWD", "NET", "DOCN"], pool)
    semi = _theme_avg(["SMH", "SOXX", "TSM", "MU"], pool)
    vix = _find(indices, "^VIX")
    wti = _find(indices, "CL=F")
    pts = []

    # 觀察點 1:軟硬體輪動 OR 最弱股支撐
    soft_names = [h["ticker"] for h in holdings if h["ticker"] in ("CRWD", "NET", "DOCN")]
    if soft is not None and semi is not None and (semi - soft) >= 1.5:
        docn = _find(holdings, "DOCN")
        pts.append({
            "h": f'軟體 vs 硬體輪動 — 組合 {"/".join(soft_names)} 的試金石',
            "ctx": f'今日軟體均 {_arrow(soft)} vs 半導體均 {_arrow(semi)},明確背離。',
            "a": '一日獲利了結,軟體 1-3 天止穩 → 軟體持股持有不動',
            "b": f'輪動延續多日 → 估值最高的 DOCN{("("+_arrow(docn["chg_pct"])+")") if docn and docn.get("chg_pct") is not None else ""} 最先承壓,考慮減碼',
            "do": '盯 IGV(軟體 ETF)能否止跌;軟體核心持股支撐是否守住'})
    elif worst:
        pts.append({
            "h": f'{worst["ticker"]} 最弱 {_arrow(worst["chg_pct"])} — 支撐攻防',
            "ctx": f'{worst["ticker"]} 今日領跌,需確認是否止穩。',
            "a": '隔日止跌收紅 → 屬個股事件,逢低留意',
            "b": '跌勢延續 + 帶量 → 趨勢轉弱,設停損、暫不接刀',
            "do": f'觀察 {worst["ticker"]} 前低支撐與成交量'})

    # 觀察點 2:最強股 / 最強主題的動能延續
    if best:
        pts.append({
            "h": f'{best["ticker"]} 最強 {_arrow(best["chg_pct"])} — 動能 vs 利多出盡',
            "ctx": f'{best["ticker"]} 今日領漲,留意是追價熱還是見高拉回。',
            "a": '隔日守住漲幅 → 動能延續,順勢持有',
            "b": '高開低走 / 量縮 → 利多出盡,勿追高、等回測',
            "do": f'觀察 {best["ticker"]} 開盤量能與前高壓力'})

    # 觀察點 3:宏觀 / 情緒 / 地緣
    macro_ctx = []
    wti_c = wti.get("chg_pct") if wti else None
    if wti and wti.get("close") is not None:
        macro_ctx.append(f'WTI {_num(wti["close"])} {_arrow(wti_c)}')
    if naaim and naaim.get("latest") is not None:
        macro_ctx.append(f'NAAIM {naaim["latest"]}')
    if fg and fg.get("score") is not None:
        macro_ctx.append(f'F&G {fg["score"]}')
    nxt = _next_catalysts(earnings, cal, report_date)
    pts.append({
        "h": '宏觀 / 情緒 / 地緣雙變數',
        "ctx": "、".join(macro_ctx) + "。" if macro_ctx else "留意數據與地緣。",
        "a": '數據偏弱 + 地緣降溫 → 降息預期回升,風險資產反彈',
        "b": '數據偏強 + 油價走高 → 通膨憂慮、Fed 偏鷹,高估值科技再壓',
        "do": f'關注接下來:{nxt}'})

    # 整體策略
    hold = [h["ticker"] for h in valid_h if h["chg_pct"] >= 0] or \
           [h["ticker"] for h in holdings if h["ticker"] in ("COHR", "VRT", "TSM", "SMH")]
    caut = [h["ticker"] for h in valid_h if h["chg_pct"] <= -2]
    for hv in ("DOCN", "NET"):  # 高估值,僅在未列入持有時提示謹慎
        if hv not in caut and hv not in hold and _find(holdings, hv):
            caut.append(hv)
    caut = [t for t in dict.fromkeys(caut) if t not in hold]  # 去重 + 不與持有衝突
    hedge = "VIX 上升 + 地緣 → 小部位 XLE(能源)/ GLD(黃金)作對沖" if (vix and (vix.get("chg_pct") or 0) > 0) \
            else "VIX 偏穩,維持現金部位即可"
    strat = (f'💡 <b>整體策略</b><br>'
             f'持有:{"、".join(hold[:6]) if hold else "—"}<br>'
             f'謹慎:{"、".join(dict.fromkeys(caut)) if caut else "—"}<br>'
             f'對沖:{hedge}<br>'
             f'下個轉折:{nxt}')
    return pts, strat


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
    bottleneck, fg, naaim, aaii, news, earnings, market_news=None, macro=None,
    is_sunday=False, narrative=None,
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
    # ⭐ LLM 深度分析:重大事件(有 narrative 時優先呈現,含因果詮釋)
    events = (narrative or {}).get("major_events") or []
    for ev in events:
        title = ev.get("title", "")
        detail = ev.get("detail", "")
        nh.append(
            f'<div style="border-left:3px solid #ea580c;background:#fff7ed;border-radius:6px;'
            f'padding:10px;margin-bottom:8px;font-size:13px;line-height:1.6;color:#7c2d12">'
            f'<b>⭐ {title}</b><br><span style="color:#9a3412">{detail}</span></div>')
    # 🔥 大盤新聞標題(色塊)。個股新聞已併入 ⑪ 核心持股。
    if market_news:
        for n in market_news[:5 if events else 7]:
            nh.append(_box(f'📰 {_newslink(n)}', "#fef9f5", "", "#7c2d12"))
    elif not events:
        nh.append('<div style="color:#94a3b8;font-size:13px">(大盤新聞暫缺)</div>')
    P.append(f'''<div style="padding:14px 16px 8px">{_title("④ 今日新聞快報 · 大盤重大事件")}
<div style="font-size:11.5px;color:#94a3b8;margin-bottom:6px">{"⭐=AI 深度分析｜" if events else ""}個股新聞請見 ⑪ 核心持股</div>{"".join(nh)}</div>''')

    # ⑤ 社群熱度 + 真偽辯論台(熱度Top5 + 資料驅動選題 + 五維評估)
    from knowledge import DEBATE_POOL, STOCK_DEBATE
    # 🔥 熱度 Top5:依當日 |漲跌| 排序
    heat_rows = _heat_top5(holdings, watchlist_data, thematics)
    heat_html = "".join(
        f'<tr style="background:{"#f8fafc" if i % 2 == 0 else "#fff"}">'
        f'<td style="padding:6px;color:#64748b">{["①","②","③","④","⑤"][i]}</td>'
        f'<td style="padding:6px;font-weight:600">{t}</td>'
        f'<td style="padding:6px">{fire}</td>'
        f'<td style="padding:6px;text-align:right;color:{_c(c)};font-weight:600">{_arrow(c)}</td>'
        f'<td style="padding:6px;color:#475569;font-size:12px">{sig}</td></tr>'
        for i, (t, c, fire, sig) in enumerate(heat_rows))
    # ⚖️ 辯論台
    debate, data_line = _pick_debate(holdings, watchlist_data, sectors, thematics,
                                     bottleneck, DEBATE_POOL, STOCK_DEBATE)
    debate_html = ""
    if debate:
        bull = "".join(f'<li>{x}</li>' for x in debate["bull"])
        bear = "".join(f'<li>{x}</li>' for x in debate["bear"])
        assess = debate["assess"]
        if isinstance(assess, dict):
            assess_html = "".join(
                f'<div style="margin-top:3px">• <b>{k}：</b>{v}</div>' for k, v in assess.items())
        else:
            assess_html = assess
        debate_html = f'''<div style="font-size:13px;font-weight:700;color:#0f172a;margin:12px 0 8px">⚖️ 辯論台：{debate["topic"]}</div>
{(f'<div style="font-size:12px;color:#64748b;margin-bottom:8px">📊 當日數據：{data_line}</div>') if data_line else ""}
<div style="display:flex;gap:8px;flex-wrap:wrap">
<div style="flex:1;min-width:200px;border:1px solid #bbf7d0;background:#f0fdf4;border-radius:8px;padding:10px;font-size:12.5px;line-height:1.55;color:#14532d"><b>🐂 多方</b><ul style="margin:4px 0 0 16px;padding:0">{bull}</ul></div>
<div style="flex:1;min-width:200px;border:1px solid #fecaca;background:#fef2f2;border-radius:8px;padding:10px;font-size:12.5px;line-height:1.55;color:#7f1d1d"><b>🐻 空方</b><ul style="margin:4px 0 0 16px;padding:0">{bear}</ul></div>
</div>
<div style="background:#eef2ff;border-radius:8px;padding:10px;margin-top:8px;font-size:12.5px;line-height:1.6;color:#3730a3"><b>📊 Claude 評估</b>{assess_html}</div>'''
    P.append(f'''<div style="padding:14px 16px 8px">{_title("⑤ 社群熱度 + 真偽辯論台", "#ea580c")}
<div style="font-size:13px;font-weight:700;color:#0f172a;margin-bottom:6px">🔥 熱度 Top 5</div>
<table style="width:100%;border-collapse:collapse;font-size:13px">{heat_html}</table>
{debate_html}</div>''')

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
    # 數據儀表板:最強 vs 最弱主題的世紀分歧(含成分股)
    dash = ""
    if theme_stats and len(theme_stats) >= 2:
        ld, lg = theme_stats[0], theme_stats[-1]
        ld_m = " / ".join(f'{tk} {_arrow(v)}' for tk, v in ld["members"][:4])
        lg_m = " / ".join(f'{tk} {_arrow(v)}' for tk, v in lg["members"][:4])
        spx_line = f'　大盤 S&P 500 {_arrow(spx["chg_pct"])}' if spx and spx.get("chg_pct") is not None else ""
        dash = (
            f'<div style="background:#0f172a;color:#e2e8f0;border-radius:8px;padding:11px;margin-bottom:10px;font-size:12.5px;line-height:1.7">'
            f'<b>📟 板塊分歧儀表板</b><br>'
            f'🟢 最強 <b>{ld["theme"]}</b> {_arrow(ld["avg"])}<br><span style="color:#94a3b8">　{ld_m}</span><br>'
            f'🔴 最弱 <b>{lg["theme"]}</b> {_arrow(lg["avg"])}<br><span style="color:#94a3b8">　{lg_m}</span>'
            f'{("<br>" + spx_line.strip()) if spx_line else ""}<br>'
            f'<span style="color:#cbd5e1">強弱差 {ld["avg"]-lg["avg"]:.2f}pp — '
            f'{"資金明確選邊、主題輪動" if (ld["avg"]-lg["avg"]) > 5 else "類股分歧溫和"}</span></div>')
    # ⭐ LLM 深度主線(有 narrative 時置頂呈現)
    storylines = (narrative or {}).get("storylines") or []
    story_html = ""
    for s in storylines:
        story_html += (
            f'<div style="border-left:3px solid #2563eb;background:#eff6ff;border-radius:6px;'
            f'padding:10px;margin-bottom:8px;font-size:13px;line-height:1.65;color:#1e3a8a">'
            f'<b>⭐ {s.get("headline","")}</b><br><span style="color:#1f2937">{s.get("body","")}</span></div>')
    P.append(f'''<div style="padding:14px 16px 8px">{_title("⑦ 產業聚焦（主題比較）")}
{story_html}{dash}<div style="font-size:11.5px;color:#94a3b8;margin-bottom:6px">各主題=代表個股當日平均，由強到弱</div>
{"".join(cards)}
<div style="background:#eef2ff;border-radius:8px;padding:11px;margin-top:10px;font-size:13px;color:#3730a3;line-height:1.6">
<b>🔍 重點分析：</b>{focus_an}</div></div>''')

    # ⑧ 廣域產業雷達(RADAR_KB 卡片 + 注入當日太空股漲跌)
    from knowledge import RADAR_KB
    rklb = _find(watchlist_data, "RKLB")
    nasa = _find(holdings, "NASA")
    live_bits = []
    if rklb and rklb.get("chg_pct") is not None:
        live_bits.append(f'RKLB {_arrow(rklb["chg_pct"])}')
    if nasa and nasa.get("chg_pct") is not None:
        live_bits.append(f'NASA(太空 ETF) {_arrow(nasa["chg_pct"])}')
    radar_cards = []
    for ci, card in enumerate(RADAR_KB.get("cards", [])):
        lines = list(card["lines"])
        if ci == 0 and live_bits:  # 本週主題卡注入即時數據
            lines.insert(0, "<b>今日:</b> " + "、".join(live_bits))
        body = "<br>".join("・" + ln for ln in lines)
        radar_cards.append(
            f'<div style="border:1px solid #e5e7eb;border-radius:8px;padding:10px;margin-bottom:8px">'
            f'<div style="font-weight:700;font-size:13.5px;color:#0f172a">{card["icon"]} {card["title"]}</div>'
            f'<div style="font-size:12.5px;color:#475569;line-height:1.65;margin-top:4px">{body}</div></div>')
    P.append(f'''<div style="padding:14px 16px 8px">{_title("⑧ 廣域產業雷達")}
<div style="font-size:11.5px;color:#94a3b8;margin-bottom:6px">本週主題：{RADAR_KB.get("weekly_theme","")}</div>
{"".join(radar_cards)}</div>''')

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

    # ⑬ 操盤指令(資料驅動多級分類:重點 / 觀察 / 監控 / 警示 / 觀察池)
    orders = []
    i = 0
    def _ord(level, text):
        nonlocal i
        i += 1
        return _row([_td(level, "left", "#1f2937", "400"), _td(text)], i % 2 == 1)
    # ★★★★ 重點:當日最強核心持股
    if best:
        bkb = HOLDINGS_KB.get(best["ticker"], {})
        orders.append(_ord("★★★★ 重點", f'{best["ticker"]} 持有,當日最強({_arrow(best["chg_pct"])});'
                           f'強勢勿追高,回檔分批{("｜"+bkb.get("催化劑")) if bkb.get("催化劑") else ""}'))
    # ⚠️ 警示:跌逾 3% 的持股(設停損)
    alerts = sorted([h for h in valid_h if h["chg_pct"] <= -3], key=lambda x: x["chg_pct"])
    for a in alerts[:3]:
        akb = HOLDINGS_KB.get(a["ticker"], {})
        orders.append(_ord("⚠️ 警示", f'{a["ticker"]} {_arrow(a["chg_pct"])},確認支撐、跌破設停損'
                           f'{("｜風險:"+akb.get("風險")) if akb.get("風險") else ""}'))
    # ★★ 觀察:小跌(0~-3%)的核心持股
    watch = sorted([h for h in valid_h if -3 < h["chg_pct"] < 0], key=lambda x: x["chg_pct"])
    for w in watch[:3]:
        orders.append(_ord("★★ 觀察", f'{w["ticker"]} {_arrow(w["chg_pct"])},屬正常回落,持有觀察'))
    # 🟢 監控:小漲/持平(非最強)的核心持股
    mons = [h for h in valid_h if h["chg_pct"] >= 0 and (not best or h["ticker"] != best["ticker"])]
    if mons:
        names = "、".join(f'{m["ticker"]}({_arrow(m["chg_pct"])})' for m in mons[:4])
        orders.append(_ord("🟢 監控", f'{names} 持有,順勢不加碼'))
    # 🌟 觀察池:組合外觀察名單
    pool_names = []
    if watchlist_data:
        w0 = watchlist_data[0]
        pool_names.append(f'{w0["ticker"]}({_arrow(w0["chg_pct"])})' if w0.get("chg_pct") is not None else w0["ticker"])
    pool_names.append("SpaceX IPO 6/12 後評估太空池")
    orders.append(_ord("🌟 觀察池", "、".join(pool_names) + " — 等催化/估值重設再進"))
    P.append(f'''<div style="padding:14px 16px 8px">{_title("⑬ 操盤指令")}
<table style="width:100%;border-collapse:collapse;font-size:13px">{"".join(orders)}</table></div>''')

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

    # ⑮ 亞太接棒(分 台/日/中/匯,資料驅動)
    asia = _asia_handoff(holdings, watchlist_data, sectors, thematics, bottleneck, indices)
    P.append(f'''<div style="padding:14px 16px 8px">{_title("⑮ 亞太接棒")}
<div style="font-size:13px;line-height:1.7;color:#1f2937">{asia}</div></div>''')

    # ⑯ 今日 3 觀察點(各含場景 A/B + 明日做什麼)+ 整體策略
    cal_obs = _load_json("manual_calendar.json")
    obs_pts, strat = _observations(holdings, valid_h, best, worst, watchlist_data, sectors,
                                   thematics, bottleneck, naaim, fg, indices, earnings,
                                   cal_obs, report_date)
    obs_html = ""
    for i, p in enumerate(obs_pts, 1):
        obs_html += (
            f'<div style="background:#fff7ed;border-radius:8px;padding:10px;margin-bottom:8px;'
            f'font-size:13px;line-height:1.6;color:#1f2937">'
            f'<b>{i}. {p["h"]}</b><br>'
            f'<span style="color:#475569">{p["ctx"]}</span><br>'
            f'<span style="color:#15803d">場景A：{p["a"]}</span><br>'
            f'<span style="color:#b91c1c">場景B：{p["b"]}</span><br>'
            f'<span style="color:#1d4ed8">👉 明日做什麼：{p["do"]}</span></div>')
    P.append(f'''<div style="padding:14px 16px 16px">{_title("⑯ 今日 3 觀察點", "#dc2626")}
<div style="font-size:14px;line-height:1.6">{obs_html}</div>
<div style="background:#0f172a;color:#e2e8f0;border-radius:8px;padding:12px;margin-top:12px;font-size:13px;line-height:1.75">{strat}</div></div>''')

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
