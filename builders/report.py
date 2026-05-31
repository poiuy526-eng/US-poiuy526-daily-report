"""組裝 16 段 Markdown 報告"""
from datetime import date


def _chg_str(chg_pct) -> str:
    if chg_pct is None:
        return "N/A"
    arrow = "▲" if chg_pct >= 0 else "▼"
    return f"{arrow} {abs(chg_pct):.2f}%"


def _price_str(close) -> str:
    return f"${close:.2f}" if close is not None else "N/A"


# ── §① 總體環境 ─────────────────────────────────────────────
def build_macro(indices: list[dict]) -> str:
    lines = ["## ① 總體環境\n"]
    lines.append("| 指標 | 最新 | 漲跌 |")
    lines.append("|---|---|---|")
    for q in indices:
        name = q.get("name", q["ticker"])
        lines.append(f"| {name} | {_price_str(q['close'])} | {_chg_str(q['chg_pct'])} |")
    return "\n".join(lines)


# ── §② Sector Heatmap ───────────────────────────────────────
def build_sector_heatmap(sectors: list[dict]) -> str:
    sorted_s = sorted(sectors, key=lambda x: x["chg_pct"] if x["chg_pct"] is not None else 0, reverse=True)
    lines = ["## ② Sector Heatmap\n"]
    lines.append("| 類股 | ETF | 漲跌 |")
    lines.append("|---|---|---|")
    for q in sorted_s:
        chg = q["chg_pct"]
        emoji = "🟢" if chg and chg > 0 else ("🔴" if chg and chg < 0 else "⬜")
        lines.append(f"| {q['name']} | {q['ticker']} | {emoji} {_chg_str(chg)} |")
    return "\n".join(lines)


# ── §③ 市場情緒指標 ──────────────────────────────────────────
def build_sentiment(fg: dict | None) -> str:
    from fetchers.sentiment import label_fg
    lines = ["## ③ 市場情緒指標\n"]
    if fg:
        score = fg["score"]
        label = label_fg(score)
        prev = fg["prev_close"]
        trend = ""
        if score is not None and prev is not None:
            diff = score - prev
            trend = f"（較昨日 {'↑' if diff >= 0 else '↓'}{abs(diff):.1f}）"
        lines.append(f"**CNN Fear & Greed:** {score} — {label}{trend}")
    else:
        lines.append("**CNN Fear & Greed:** (資料暫缺)")
    lines.append("\n**NAAIM Exposure Index:** (週三更新，資料暫缺)")
    lines.append("\n**AAII Investor Sentiment:** (週四更新，資料暫缺)")
    return "\n".join(lines)


# ── §④ 今日新聞 ──────────────────────────────────────────────
def build_news(news: dict[str, list[dict]]) -> str:
    lines = ["## ④ 今日新聞（AI 軟體三檔）\n"]
    for tk, items in news.items():
        lines.append(f"### {tk}")
        if not items:
            lines.append("(資料暫缺)")
        else:
            for n in items:
                src = f" _{n['source']}_" if n["source"] else ""
                link = f" [↗]({n['url']})" if n["url"] else ""
                lines.append(f"- {n['title']}{src}{link}")
        lines.append("")
    return "\n".join(lines)


# ── §⑤ 社群熱度 ─────────────────────────────────────────────
def build_social() -> str:
    return "## ⑤ 社群熱度 + 辯論台\n\n(後期接入社群資料，結構預留)"


# ── §⑥ 瓶頸輪動 ─────────────────────────────────────────────
def build_bottleneck(nodes: dict[str, list[dict]]) -> str:
    lines = ["## ⑥ 瓶頸輪動（資金流向）\n"]
    lines.append("| 節點 | 標的 | 最新 | 漲跌 |")
    lines.append("|---|---|---|---|")
    for node, tickers in nodes.items():
        for q in tickers:
            lines.append(f"| {node} | {q['ticker']} | {_price_str(q['close'])} | {_chg_str(q['chg_pct'])} |")
    return "\n".join(lines)


# ── §⑦ 產業聚焦 ─────────────────────────────────────────────
def build_industry_focus() -> str:
    return "## ⑦ 產業聚焦\n\n(本週主題輪動：請手動填入或後期接入)"


# ── §⑧ 廣域產業雷達 ──────────────────────────────────────────
def build_radar(is_sunday: bool = False) -> str:
    if is_sunday:
        return "## ⑧ 廣域產業雷達\n\n(週日深度版 — 主題輪動完整展開，資料待接入)"
    return "## ⑧ 廣域產業雷達（簡版）\n\n(2–3 非 AI 產業摘要，資料待接入)"


# ── §⑨ 產業學堂（週日）────────────────────────────────────────
def build_school(is_sunday: bool = False) -> str:
    if not is_sunday:
        return ""
    return "## ⑨ 產業學堂\n\n(週日專屬 — 本週主題深度解析)"


# ── §⑩ 低點布局（週日）───────────────────────────────────────
def build_dip(is_sunday: bool = False) -> str:
    if not is_sunday:
        return ""
    return "## ⑩ 低點布局\n\n(週日專屬 — 回調標的掃描)"


# ── §⑪ 核心持股 ─────────────────────────────────────────────
def build_core_holdings(holdings: list[dict]) -> str:
    lines = ["## ⑪ 核心持股（10 檔）\n"]
    lines.append("| 標的 | 最新 | 漲跌 | 成交量 |")
    lines.append("|---|---|---|---|")
    for q in holdings:
        vol = f"{q['volume']:,}" if q.get("volume") else "N/A"
        lines.append(f"| {q['ticker']} | {_price_str(q['close'])} | {_chg_str(q['chg_pct'])} | {vol} |")
    return "\n".join(lines)


# ── §⑫ 十倍股觀察池 ──────────────────────────────────────────
def build_watchlist(watchlist: list[dict]) -> str:
    lines = ["## ⑫ 十倍股觀察池\n"]
    lines.append("| 標的 | 最新 | 漲跌 |")
    lines.append("|---|---|---|")
    for q in watchlist:
        lines.append(f"| {q['ticker']} | {_price_str(q['close'])} | {_chg_str(q['chg_pct'])} |")
    return "\n".join(lines)


# ── §⑬ 操盤指令 ─────────────────────────────────────────────
def build_trading_orders() -> str:
    return "## ⑬ 操盤指令\n\n(人工判斷為主 — 請根據今日行情手動填入進出場指令)"


# ── §⑭ 財報雷達 ─────────────────────────────────────────────
def build_earnings_radar() -> str:
    return "## ⑭ 財報雷達\n\n(近期持股/觀察池財報日 — 資料待接入)"


# ── §⑮ 亞太接棒 ─────────────────────────────────────────────
def build_asia_relay() -> str:
    return "## ⑮ 亞太接棒\n\n(台股/亞股對應標的 — 資料待接入)"


# ── §⑯ 今日 3 觀察點 ────────────────────────────────────────
def build_three_points(holdings: list[dict], fg: dict | None) -> str:
    lines = ["## ⑯ 今日 3 觀察點\n"]
    # 自動生成：取漲跌最大的三檔
    valid = [q for q in holdings if q["chg_pct"] is not None]
    top_mover = sorted(valid, key=lambda x: abs(x["chg_pct"]), reverse=True)[:3]
    for i, q in enumerate(top_mover, 1):
        lines.append(f"{i}. **{q['ticker']}** 今日 {_chg_str(q['chg_pct'])}，值得關注")
    if not top_mover:
        lines.append("(資料暫缺)")
    return "\n".join(lines)


# ── §⓪ 60 秒 Brief（由其他段落摘要生成）────────────────────
def build_brief(indices: list[dict], holdings: list[dict], fg: dict | None) -> str:
    spx = next((q for q in indices if q["ticker"] == "^GSPC"), None)
    ndx = next((q for q in indices if q["ticker"] == "^IXIC"), None)
    vix = next((q for q in indices if q["ticker"] == "^VIX"), None)

    spx_str = f"S&P 500 {_chg_str(spx['chg_pct'])}" if spx else ""
    ndx_str = f"Nasdaq {_chg_str(ndx['chg_pct'])}" if ndx else ""
    vix_str = f"VIX {_price_str(vix['close'])}" if vix else ""

    from fetchers.sentiment import label_fg
    fg_str = f"Fear & Greed {fg['score']} {label_fg(fg['score'])}" if fg else "Fear & Greed (暫缺)"

    valid = [q for q in holdings if q["chg_pct"] is not None]
    best = max(valid, key=lambda x: x["chg_pct"]) if valid else None
    worst = min(valid, key=lambda x: x["chg_pct"]) if valid else None

    lines = ["## ⓪ 60 秒 Brief\n"]
    parts = [p for p in [spx_str, ndx_str, vix_str] if p]
    lines.append("**大盤：** " + "　".join(parts))
    lines.append(f"\n**情緒：** {fg_str}")
    if best:
        lines.append(f"\n**最強：** {best['ticker']} {_chg_str(best['chg_pct'])}")
    if worst:
        lines.append(f"\n**最弱：** {worst['ticker']} {_chg_str(worst['chg_pct'])}")
    return "\n".join(lines)


# ── 主組裝函數 ───────────────────────────────────────────────
def build_full_report(
    report_date: date,
    indices: list[dict],
    sectors: list[dict],
    holdings: list[dict],
    watchlist_data: list[dict],
    bottleneck: dict,
    fg: dict | None,
    news: dict,
    is_sunday: bool = False,
) -> str:
    sections = []

    header = f"# 美股日報 {report_date.strftime('%Y-%m-%d')}{'（週日深度版）' if is_sunday else ''}\n"
    sections.append(header)

    sections.append(build_brief(indices, holdings, fg))
    sections.append(build_macro(indices))
    sections.append(build_sector_heatmap(sectors))
    sections.append(build_sentiment(fg))
    sections.append(build_news(news))
    sections.append(build_social())
    sections.append(build_bottleneck(bottleneck))
    sections.append(build_industry_focus())
    sections.append(build_radar(is_sunday))
    school = build_school(is_sunday)
    if school:
        sections.append(school)
    dip = build_dip(is_sunday)
    if dip:
        sections.append(dip)
    sections.append(build_core_holdings(holdings))
    sections.append(build_watchlist(watchlist_data))
    sections.append(build_trading_orders())
    sections.append(build_earnings_radar())
    sections.append(build_asia_relay())
    sections.append(build_three_points(holdings, fg))

    return "\n\n---\n\n".join(sections)
