from datetime import date

# --- 核心持股 ---
CORE_HOLDINGS = ["TSLA", "CRCL", "CRWD", "GOOGL", "SMH", "TSM", "VRT", "COHR", "NET", "DOCN"]

# --- 觀察池 ---
WATCHLIST = ["RKLB"]

# --- AI 軟體新聞三檔 ---
NEWS_TICKERS = ["CRWD", "NET", "DOCN"]

# --- Sector ETF ---
SECTOR_ETFS = {
    "科技 XLK": "XLK",
    "金融 XLF": "XLF",
    "能源 XLE": "XLE",
    "醫療 XLV": "XLV",
    "工業 XLI": "XLI",
    "非必需消費 XLY": "XLY",
    "必需消費 XLP": "XLP",
    "公用事業 XLU": "XLU",
    "原物料 XLB": "XLB",
    "房地產 XLRE": "XLRE",
    "通訊 XLC": "XLC",
}

# --- 瓶頸輪動五節點 ---
BOTTLENECK_NODES = {
    "HBM/DRAM 記憶體": ["MU"],
    "光通訊互連": ["COHR", "GLW"],
    "AI 電力": ["VRT", "GEV", "CEG"],
    "銅/金": ["FCX", "GLD", "GOLD"],
    "上游金屬/稀土": ["MP", "ALB"],
}

# --- 大盤指數 ---
INDICES = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "Dow Jones": "^DJI",
    "Russell 2000": "^RUT",
    "VIX": "^VIX",
}

# --- 債券/匯率 ---
MACRO = {
    "美債10Y": "^TNX",
    "美元指數": "DX-Y.NYB",
    "黃金": "GC=F",
    "原油": "CL=F",
}

# --- CNN Fear & Greed ---
FEAR_GREED_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

# --- 輸出設定 ---
OUTPUT_DIR = "output"
REPORT_DATE = date.today()

# --- 推送設定(預設關閉)---
AUTO_SEND_NOTION = False
AUTO_SEND_GMAIL = False
GMAIL_RECIPIENT = "poiuy526@gmail.com"
NOTION_PARENT_ID = "6aa7b6ca-147c-40df-9de0-083cbeb13978"

# --- Gmail SMTP 寄信設定 ---
# 寄件帳號(你的 Gmail)
GMAIL_SENDER = "poiuy526@gmail.com"
# 應用程式密碼:不要寫在這裡!從環境變數 GMAIL_APP_PASSWORD 讀取
# 設定方式(PowerShell): $env:GMAIL_APP_PASSWORD = "你的16位應用程式密碼"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
