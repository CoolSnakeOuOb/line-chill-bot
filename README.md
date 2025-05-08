
# LINE CHILL 放鬆 FUN暑假客服機器人

本專案是一個串接 LINE Messaging API 與 Google Gemini API 的 LINE 機器人，能回答暑假補助活動相關問題，並提供常見問題選單。

---

## 📦 專案結構

```
.
├── chill.py              # 主程式
├── .env                  # 環境變數檔案（實際運行需建立）
├── .env.example          # 範例環境變數（不含金鑰）
├── requirements.txt      # 套件需求
├── README.md             # 說明文件（本檔）
```

---

## 🖥️ 本地端執行

### 1. 安裝 Python 環境

請先安裝 Python 3.9+，並在終端機執行以下指令：

```bash
python -m venv venv
source venv/bin/activate  # Windows 用戶請改用 venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 建立 `.env` 檔案

在根目錄下建立 `.env` 檔案，填入以下內容：

```ini
LINE_CHANNEL_ACCESS_TOKEN=你的Line金鑰
LINE_CHANNEL_SECRET=你的Line密鑰
GEMINI_API_KEY=你的Gemini API金鑰
```

（可參考 `.env.example`）

### 3. 執行機器人

```bash
python chill.py
```

若需對外測試（連接 LINE），可搭配 [ngrok](https://ngrok.com/)：

```bash
ngrok http 5000
```

將產出的網址填入 LINE Developer Console 中的 Webhook URL：

```
https://你的-ngrok-id.ngrok-free.app/callback
```

---

## ☁️ Render 雲端部署（推薦）

### 1. 上傳 GitHub

建立一個 GitHub Repository，上傳以下檔案：

- chill.py
- .env.example
- requirements.txt
- .gitignore

（不要上傳 `.env` 正式金鑰檔）

### 2. Render 設定

1. 到 https://dashboard.render.com
2. 點「New」→ Web Service
3. 選擇 GitHub 專案
4. 設定環境變數（Environment）如下：
   - LINE_CHANNEL_ACCESS_TOKEN
   - LINE_CHANNEL_SECRET
   - GEMINI_API_KEY
5. Python build command：`pip install -r requirements.txt`
6. Start command：`python chill.py`
7. 點選「Deploy」部署

### 3. 設定 LINE Webhook

Render 部署完成後，複製它的網址（如 `https://line-chill-bot.onrender.com/callback`）到 LINE Developers 中 Webhook URL 欄位 → 按 `Verify`。

---

## ✅ 成功後你可以：

- 在 LINE 加入該 bot
- 說「menu」或「hi」觸發常見問題選單
- 詢問補助相關內容，將由 Gemini 回覆



