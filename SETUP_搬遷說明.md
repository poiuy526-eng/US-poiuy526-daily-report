# 換電腦搬遷說明

## 要搬的東西

整個 `us-daily-report/` 資料夾就是全部程式。但有**一個不在資料夾裡**的東西要另外設定:
- 🔑 **Gmail 應用程式密碼**(環境變數 `GMAIL_APP_PASSWORD`)——基於安全,密碼不寫在程式碼裡,新電腦要重設。

---

## 新電腦設定步驟

### 1. 裝 Python
到 https://python.org 下載 Python 3.11+,安裝時**勾選「Add Python to PATH」**。

### 2. 複製專案
把整個 `us-daily-report/` 資料夾複製過去(用 USB / 雲端 / Git 皆可)。
> `output/` 裡的舊報告可不帶。`__pycache__/` 不用帶。

### 3. 裝依賴
在專案資料夾開 PowerShell:
```powershell
python -m pip install -r requirements.txt
```

### 4. 設 Gmail 應用程式密碼(只需一次)
```powershell
setx GMAIL_APP_PASSWORD "你的16碼應用程式密碼"
```
> 密碼從 https://myaccount.google.com/apppasswords 取得(需先開兩步驟驗證)。
> 設完要**開新的 PowerShell 視窗**才讀得到。

### 5. 測試
```powershell
python senders\gmail_smtp.py        # 寄測試信
python main.py                      # 產生今天日報(不寄)
python main.py --send-gmail         # 產生並寄出
```

---

## 不需要搬的東西

- ❌ `__pycache__/`、`output/` 舊檔——可重新產生
- ❌ Gmail 密碼**不要**寫進任何檔案帶走,新電腦重設即可
- ❌ Claude Code 的 MCP 連接器設定——本專案已改用 SMTP 自寄,與 MCP 無關

---

## 建議:用 Git 管理(更省事)

如果想之後同步更方便:
```powershell
cd us-daily-report
git init
git add .
git commit -m "美股日報專案"
# 推到你的 GitHub 私有 repo
```
> ⚠️ `.gitignore` 已設定排除密碼相關。**絕不要** commit 任何含密碼的檔案。
> 換電腦只要 `git clone` + 上面步驟 3~4 即可。

---

## 路徑注意

程式內部用相對路徑(`__file__` 基準),搬到任何資料夾都能跑。
唯一要注意:執行時若用完整 python 路徑,記得換成新電腦的 python 位置,
或直接用 `python`(已加入 PATH 的話)。
