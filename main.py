"""美股日報產生器 — 進入點"""
import argparse
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    OUTPUT_DIR, CORE_HOLDINGS, WATCHLIST, GMAIL_RECIPIENT,
    AUTO_SEND_NOTION, AUTO_SEND_GMAIL, NOTION_PARENT_ID
)
from fetchers.prices import fetch_core_holdings, fetch_indices, fetch_sector_etfs, fetch_bottleneck_nodes
from fetchers.sentiment import fetch_fear_greed
from fetchers.news import fetch_stock_news
from builders.report import build_full_report


def parse_args():
    p = argparse.ArgumentParser(description="美股日報產生器")
    p.add_argument("--date", default=None, help="報告日期 YYYY-MM-DD（預設今天）")
    p.add_argument("--sunday", action="store_true", help="強制產生週日深度版")
    p.add_argument("--send-gmail", action="store_true", help="強制寄送 Gmail（覆蓋 config 設定）")
    p.add_argument("--send-notion", action="store_true", help="強制推送 Notion")
    return p.parse_args()


def main():
    args = parse_args()

    report_date = date.today()
    if args.date:
        report_date = datetime.strptime(args.date, "%Y-%m-%d").date()

    is_sunday = args.sunday or (report_date.weekday() == 6)

    print(f"[INFO] 產生日報：{report_date}  {'(週日深度版)' if is_sunday else '(平日版)'}")

    # ── 抓資料 ──
    print("[INFO] 抓取指數資料...")
    indices = fetch_indices()

    print("[INFO] 抓取 Sector ETF...")
    sectors = fetch_sector_etfs()

    print("[INFO] 抓取主題 ETF...")
    from fetchers.prices import fetch_thematic_etfs
    thematics = fetch_thematic_etfs()

    print("[INFO] 抓取核心持股...")
    all_holdings = fetch_core_holdings()
    holdings = [q for q in all_holdings if q["ticker"] in CORE_HOLDINGS]
    watchlist_data = [q for q in all_holdings if q["ticker"] in WATCHLIST]

    print("[INFO] 抓取瓶頸輪動...")
    bottleneck = fetch_bottleneck_nodes()

    print("[INFO] 抓取情緒指標(F&G / NAAIM / AAII)...")
    fg = fetch_fear_greed()
    from fetchers.naaim import fetch_naaim
    from fetchers.aaii import fetch_aaii
    naaim = fetch_naaim()
    aaii = fetch_aaii()

    print("[INFO] 抓取財報日...")
    from fetchers.earnings import fetch_earnings_dates
    earnings = fetch_earnings_dates()

    print("[INFO] 抓取新聞(大盤 + 個股)...")
    from fetchers.news import fetch_market_news
    market_news = fetch_market_news(max_items=6)
    # 三劍客 + 全部持股 + 觀察池都抓,新聞更豐富
    news = fetch_stock_news(tickers=list(dict.fromkeys(CORE_HOLDINGS + WATCHLIST)), max_per_ticker=2)

    print("[INFO] 新聞翻譯成繁中...")
    from utils.translate import translate_news, translate_list
    translate_news(news)
    translate_list(market_news)

    # ── 組報告 ──
    print("[INFO] 組裝報告...")
    report_md = build_full_report(
        report_date=report_date,
        indices=indices,
        sectors=sectors,
        holdings=holdings,
        watchlist_data=watchlist_data,
        bottleneck=bottleneck,
        fg=fg,
        news=news,
        is_sunday=is_sunday,
    )

    from builders.mobile_html import build_mobile_html
    report_html = build_mobile_html(
        report_date=report_date,
        indices=indices, sectors=sectors, thematics=thematics,
        holdings=holdings, watchlist_data=watchlist_data,
        bottleneck=bottleneck, fg=fg, naaim=naaim, aaii=aaii,
        news=news, market_news=market_news, earnings=earnings, is_sunday=is_sunday,
    )

    # ── 存本地（用專案根目錄為基準，避免相對路徑跑掉）──
    out_dir = OUTPUT_DIR if os.path.isabs(OUTPUT_DIR) else os.path.join(os.path.dirname(__file__), OUTPUT_DIR)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{report_date}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    html_path = os.path.join(out_dir, f"{report_date}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(report_html)
    print(f"[OK] 報告已存至：{out_path}")
    print(f"[OK] 手機版 HTML：{html_path}")

    # ── Gmail 推送 ──
    send_gmail = args.send_gmail or AUTO_SEND_GMAIL
    if send_gmail:
        print("[INFO] 寄送 Gmail（SMTP）...")
        from senders.gmail_smtp import send_report
        subject = f"美股日報 {report_date.strftime('%Y-%m-%d')}"
        send_report(subject=subject, body_md=report_md,
                    recipient=GMAIL_RECIPIENT, html_body=report_html)
    else:
        print("[INFO] Gmail 推送已關閉（用 --send-gmail 或設 AUTO_SEND_GMAIL=True 開啟）")

    return report_md, out_path


if __name__ == "__main__":
    main()
