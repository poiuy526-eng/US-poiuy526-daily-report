"""LLM 敘事產生器 — 用 Anthropic API 生成 §④ 重大事件 / §⑦ 主線深度分析(繁中)。

設計原則:
- API key 走環境變數 ANTHROPIC_API_KEY(不寫死),與 GMAIL_APP_PASSWORD 一致。
- 優雅降級:沒有 key、沒裝 anthropic、或 API 失敗 → 回傳 None,builder 自動 fallback。
- prompt caching:穩定的 system prompt(角色 + 規格)標 cache_control,降低重複成本。
- 結構化輸出:用 output_config.format(json_schema)強制回傳 {major_events, storylines}。
- 數據只引用 fetcher 已驗證的即時報價/標題,LLM 只做「分析詮釋」,不杜撰數字。
"""
import os
import json

MODEL = "claude-opus-4-8"

# 穩定的系統提示(跨日不變 → 可快取)。只放角色與輸出規格,不放當日數據。
_SYSTEM = """你是「美股日報 v14」的資深財經分析師,為台灣主動投資人 poiuy526 撰寫繁體中文深度分析。

任務:依使用者提供的「當日已驗證數據 + 新聞標題」,生成兩個段落的分析 prose:
1. major_events(§④ 今日重大事件):2–4 條。每條 title 為一句話事件標題,detail 為 2–3 句因果分析(為什麼發生、對該股/組合的意義)。
2. storylines(§⑦ 產業聚焦主線):2–3 條。每條 headline 為「主線X:標題」格式,body 為 3–5 句深度敘事(資金邏輯、板塊分歧、對組合連鎖反應)。

嚴格規則:
- 只能使用使用者提供的數字。嚴禁杜撰或推測任何未提供的價格/百分比。
- 可引用新聞標題作為事件脈絡,但若標題未含明確數字,不要自行補數字。
- 風格:金融時報早報感,精簡(每點 1–5 句),專業但好讀,繁體中文。
- 聚焦「分析詮釋」而非複述報價(報價表另有段落呈現)。
- 組合核心持股:TSLA / CRCL / CRWD / GOOGL / SMH / TSM / VRT / COHR / NET / DOCN。
- 不要用 markdown 標記符號(*、#),純文字句子即可。"""

_SCHEMA = {
    "type": "object",
    "properties": {
        "major_events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                },
                "required": ["title", "detail"],
                "additionalProperties": False,
            },
        },
        "storylines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "headline": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["headline", "body"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["major_events", "storylines"],
    "additionalProperties": False,
}


def _fmt_quotes(quotes, limit=None):
    rows = []
    for q in (quotes or []):
        c = q.get("chg_pct")
        if c is None:
            continue
        arrow = f"+{c:.2f}%" if c >= 0 else f"{c:.2f}%"
        rows.append(f'{q.get("name", q["ticker"])}({q["ticker"]}) {arrow}')
        if limit and len(rows) >= limit:
            break
    return "、".join(rows)


def _fmt_news(news_dict, market_news):
    lines = []
    for n in (market_news or [])[:6]:
        t = n.get("title_zh") or n.get("title", "")
        if t:
            lines.append(f'[大盤] {t}')
    if isinstance(news_dict, dict):
        for tk, items in news_dict.items():
            for n in (items or [])[:1]:
                t = n.get("title_zh") or n.get("title", "")
                if t:
                    lines.append(f'[{tk}] {t}')
    return "\n".join(lines[:20])


def generate_narrative(report_date, indices=None, holdings=None, sectors=None,
                       thematics=None, bottleneck=None, news=None, market_news=None,
                       fg=None, naaim=None, aaii=None):
    """回傳 {"major_events": [...], "storylines": [...]} 或 None(降級)。"""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[INFO] 未設定 ANTHROPIC_API_KEY,略過 LLM 敘事(用結構化 fallback)。")
        return None
    try:
        import anthropic
    except ImportError:
        print("[INFO] 未安裝 anthropic 套件(pip install anthropic),略過 LLM 敘事。")
        return None

    # 組當日數據摘要(只用已驗證報價 + 標題)
    all_sec = (sectors or []) + (thematics or [])
    sent = []
    if naaim and naaim.get("latest") is not None:
        sent.append(f'NAAIM {naaim["latest"]}')
    if fg and fg.get("score") is not None:
        sent.append(f'F&G {fg["score"]}')
    if aaii and aaii.get("bullish") is not None:
        sent.append(f'AAII 多{aaii.get("bullish")}/空{aaii.get("bearish")}')

    user_content = f"""日期:{report_date}

【指數/商品】
{_fmt_quotes(indices)}

【核心持股】
{_fmt_quotes(holdings)}

【類股/主題 ETF】
{_fmt_quotes(all_sec)}

【市場情緒】
{"、".join(sent) if sent else "(暫缺)"}

【今日新聞標題】
{_fmt_news(news, market_news)}

請依規格產生 major_events 與 storylines。"""

    try:
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            thinking={"type": "adaptive"},
            output_config={
                "effort": "medium",  # 寫作任務,成本/品質平衡;可調 high
                "format": {"type": "json_schema", "schema": _SCHEMA},
            },
            system=[{
                "type": "text",
                "text": _SYSTEM,
                "cache_control": {"type": "ephemeral"},  # 穩定前綴 → 可快取
            }],
            messages=[{"role": "user", "content": user_content}],
        )
        text = next((b.text for b in resp.content if b.type == "text"), None)
        if not text:
            print("[INFO] LLM 回傳空內容,略過敘事。")
            return None
        data = json.loads(text)
        u = resp.usage
        print(f"[OK] LLM 敘事產生:{len(data.get('major_events', []))} 事件 / "
              f"{len(data.get('storylines', []))} 主線 "
              f"(in={u.input_tokens}, cache_read={getattr(u, 'cache_read_input_tokens', 0)}, "
              f"out={u.output_tokens})")
        return data
    except anthropic.AuthenticationError:
        print("[ERROR] ANTHROPIC_API_KEY 無效,略過 LLM 敘事。")
        return None
    except Exception as e:
        print(f"[WARN] LLM 敘事產生失敗,降級為結構化 fallback: {e}")
        return None
