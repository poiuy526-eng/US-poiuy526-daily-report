"""透過 Gmail SMTP 自動寄送日報 — 應用程式密碼走環境變數,不寫死"""
import os
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import GMAIL_SENDER, GMAIL_RECIPIENT, SMTP_HOST, SMTP_PORT


def markdown_to_html(md: str) -> str:
    """極簡 Markdown → HTML(表格 + 標題 + 粗體),供 email 用"""
    lines = md.split("\n")
    html = ["<div style=\"font-family:-apple-system,Segoe UI,Arial,sans-serif;"
            "max-width:760px;margin:0 auto;color:#1a1a1a\">"]
    in_table = False
    for ln in lines:
        s = ln.strip()
        if s.startswith("|") and "---" in s:
            continue  # 表格分隔線
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not in_table:
                html.append("<table style=\"border-collapse:collapse;width:100%;"
                            "margin:8px 0;font-size:0.9em\">")
                in_table = True
            row = "".join(
                f"<td style=\"padding:6px 10px;border-bottom:1px solid #e5e7eb\">{c}</td>"
                for c in cells)
            html.append(f"<tr>{row}</tr>")
            continue
        if in_table:
            html.append("</table>")
            in_table = False
        if s.startswith("# "):
            html.append(f"<h1 style=\"border-bottom:3px solid #2563eb;padding-bottom:8px\">{s[2:]}</h1>")
        elif s.startswith("## "):
            html.append(f"<h2 style=\"color:#2563eb;border-left:4px solid #2563eb;padding-left:10px\">{s[3:]}</h2>")
        elif s.startswith("### "):
            html.append(f"<h3>{s[4:]}</h3>")
        elif s.startswith("> "):
            html.append(f"<blockquote style=\"color:#374151;border-left:3px solid #d1d5db;"
                        f"padding-left:10px;margin:6px 0\">{s[2:]}</blockquote>")
        elif s == "---":
            html.append("<hr style=\"border:none;border-top:1px solid #e5e7eb;margin:16px 0\">")
        elif s == "":
            html.append("<br>")
        else:
            html.append(f"<p style=\"margin:4px 0\">{s}</p>")
    if in_table:
        html.append("</table>")
    html.append("</div>")
    return "\n".join(html)


def send_report(subject: str, body_md: str,
                recipient: str = None, html_body: str = None) -> bool:
    """寄送日報。回傳 True/False。"""
    app_pw = os.environ.get("GMAIL_APP_PASSWORD")
    if not app_pw:
        print("[ERROR] 找不到環境變數 GMAIL_APP_PASSWORD。")
        print("        請先設定(PowerShell): $env:GMAIL_APP_PASSWORD = \"你的應用程式密碼\"")
        return False

    recipient = recipient or GMAIL_RECIPIENT
    if html_body is None:
        html_body = markdown_to_html(body_md)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_SENDER
    msg["To"] = recipient
    msg.attach(MIMEText(body_md, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(GMAIL_SENDER, app_pw)
            server.sendmail(GMAIL_SENDER, [recipient], msg.as_string())
        print(f"[OK] 已寄送日報至 {recipient}")
        return True
    except Exception as e:
        print(f"[ERROR] 寄信失敗: {e}")
        return False


if __name__ == "__main__":
    # 單獨測試:寄一封測試信
    ok = send_report(
        subject="美股日報 — SMTP 測試",
        body_md="# 測試\n\n這是一封 SMTP 測試信。\n\n> 如果你收到了,代表自動寄信設定成功。",
    )
    sys.exit(0 if ok else 1)
