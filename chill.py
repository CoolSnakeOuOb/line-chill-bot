from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage
)
from linebot.models import FollowEvent
import requests
import os
from dotenv import load_dotenv

# 載入 .env
load_dotenv()
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 活動說明
activity_info = """
你是新北捷運公司的客服機器人，專門協助同仁了解「CHILL放鬆 全家加碼 FUN 暑假」活動補助的相關規定。請用親切、簡單的語氣回答問題，幫助同仁輕鬆掌握申請流程與補助範圍。

📌 注意事項：
- 僅回答與本次暑假補助活動有關的問題，若無關請回覆：「很抱歉，我只能回答暑假補助活動相關的問題唷～」
- 回覆時請盡量以口語化、易懂的方式說明。
- 所有補助都需在同月份實報實銷，且每人只能申請一次，補助上限為新台幣 3000 元。

📚 活動資訊：
🔹 活動期間：114 年 6 月 1 日至 11 月 30 日
🔹 對象資格：限本公司「全職從業人員」（員編需為 M 開頭的同仁）
🔹 核銷期限：每月 1 日至月底消費、隔月 20 日至 25 日繳交申請表

✅ 可補助項目（限國內場館及活動）：
1️⃣ 做運動：
- 國民運動中心票券（年票、月票、日票）
- 各式運動場地租用費（羽球、籃球等）
- 健身房會員費、教練費
- 運動賽事門票（如棒球、籃球賽）

2️⃣ 享文藝：
- 展覽、歌仔戲、音樂劇、演唱會、電影票
- 博物館、美術館門票（不含紀念品店）

3️⃣ FUN假趣：
- 動物園、海洋館、遊樂園門票（園內消費不補助）

4️⃣ 全家 FUN 暑假大禮包：
- 限於十四張店購買的大禮包，每包 500 元
- 回饋點數最高 800 點（如購買 3,000 元可得）

🚫 不可補助項目：
- 餐飲（如星巴克、夜市等）
- 交通與住宿費（高鐵、旅館等）
- 非法或博弈性活動（如彩券、賭場）
- 遊戲點數、線上會員費（如 Netflix、Disney+）
- 商品購買（如運動鞋、圖書）

📝 報帳需檢附：
- 發票（需有統編：69278085）
- 門票與活動照片（需可辨識同仁與活動場地）
- 消費明細
- 存摺影本（核銷用）
- 活動申請表（請用公司 MAIL 收取後列印、簽章並繳交）

📮 報帳流程：
1. 填寫 Google 表單 ➜ https://forms.gle/sxLw18GsMjjYEKEv6
2. 列印申請表，貼上憑證與簽章
3. 每月 20～25 日交給人資室張羽呈承辦人
4. 不符規定者會通知退件修改

📸 照片補充：
- 若憑證為門票，請附上活動現場照片（需可辨識人與地點）
- 若無消費明細，也需用照片佐證活動內容

"""

# Gemini 回應
def call_gemini_api(user_input):
    prompt = f"{activity_info}\n\n使用者問題：{user_input}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        print("🔄 Gemini API 回傳內容：", result, flush=True)
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("❌ 發生錯誤：", e, flush=True)
        return "很抱歉，我暫時無法回應。"

# Flex 選單

def send_flex_menu(event):
    flex_message = FlexSendMessage(
        alt_text='請選擇你想問的問題',
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "💬 想問什麼呢？", "weight": "bold", "size": "md"},
                    {"type": "text", "text": "點選以下問題快速詢問", "size": "sm", "color": "#555555", "margin": "md"}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "✔ 哪些可以報帳？", "text": "哪些可以報帳？"},
                        "style": "secondary"
                    },
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "✖ 哪些不能報？", "text": "哪些不能報帳？"},
                        "style": "secondary"
                    },
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "🧾 發票遺失怎麼辦？", "text": "發票遺失怎麼辦？"},
                        "style": "secondary"
                    },
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "📸 一定要附活動照片嗎？", "text": "一定要附活動照片嗎？"},
                        "style": "secondary"
                    }
                ]
            }
        }
    )
    print("📤 傳送 Flex 選單", flush=True)
    line_bot_api.reply_message(event.reply_token, flex_message)

@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_data(as_text=True)
    signature = request.headers['X-Line-Signature']
    handler.handle(body, signature)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()
    print(f"🟢 使用者輸入：{user_input}", flush=True)

    if user_input.lower() in ["menu", "選單", "我要問問題", "hi", "hello"]:
        send_flex_menu(event)
    else:
        reply_text = call_gemini_api(user_input)
        print(f"🤖 Gemini 回覆：{reply_text}", flush=True)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

    
