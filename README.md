# LINE Chill Bot 說明文件

這是一個使用 Python + Flask 架設的 LINE Bot，用於回答「CHILL放鬆 全家加碼 FUN 暑假」補助活動相關問題。

---

## 📁 專案結構

```
.
├── chill.py              # 主程式
├── .env                  # 環境變數檔案（實際運行需建立）
├── .env.example          # 範例環境變數（不含金鑰）
├── faq_data.json         # FAQ 問答資料（支援語意相近問題）
├── requirements.txt      # 套件需求
├── README.md             # 說明文件（本檔）

```

> 💡 若要本地測試 Webhook，可[自行下載 ngrok](https://ngrok.com/download)，

---

## 🛠️ 安裝與執行（本地）

### 1. 建立虛擬環境並安裝套件

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 建立 `.env` 檔案

請參考 `.env.example` 並填入自己的金鑰：

```
LINE_CHANNEL_ACCESS_TOKEN=你的Line Token
LINE_CHANNEL_SECRET=你的Line Secret
GEMINI_API_KEY=你的Gemini API 金鑰
```

### 3. 啟動 Flask

```bash
python chill.py
```

### 4. 開啟 ngrok 對外連線（可選）

```bash
ngrok http 5000
```

> ✅ 複製顯示的 URL，如 `https://xxxxx.ngrok-free.app`，到 LINE Developer Webhook 設定頁面。

---

## 🚀 Render 雲端部署教學

Render 是一個免費雲端平台，可用來部署 Python Flask Web App。

### ✅ 步驟如下：

1. 📤 **將你的程式碼推到 GitHub 倉庫**（包含 `.env.example`, `requirements.txt`, `chill.py`, `faq_data.json`）

2. 🌐 **到 [https://render.com](https://render.com) 註冊帳號，並建立新的 Web Service**

3. 設定以下內容：

   * **Environment**: Python 3
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `python chill.py`
   * **Environment Variables**：

     * `LINE_CHANNEL_ACCESS_TOKEN`、`LINE_CHANNEL_SECRET`、`GEMINI_API_KEY`

4. Render 建立完成後會提供一個網址，例如：

   ```
   https://line-chill-bot.onrender.com
   ```

5. ✨ **到 LINE Developer Console 將 Webhook URL 改為：**

   ```
   https://line-chill-bot.onrender.com/callback
   ```

6. 點擊 Verify，應該會看到 success！代表部署完成。

---

## 📌 注意事項

* Render 的免費方案可能會休眠，首次請求較慢

## ✅ 成功後你可以：

- 在 LINE 加入該 bot
- 說「menu」或「hi」觸發常見問題選單
- 詢問補助相關內容，將由 Gemini 回覆



