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
你是新北捷運公司的客服機器人，負責回答「CHILL放鬆 全家加碼 FUN 暑假」活動的補助問題。請使用親切、簡單的語氣回應員工。

📌 注意事項：
- 請根據下列活動內容回答問題。
- 若問題與補助活動無關，請回覆：「很抱歉，我只能回答暑假補助活動相關的問題唷～」

📚 活動說明：
活動期間：114年6月1日至11月30日。
補助上限：每人最高3000元，限報一次，需當月實報實銷。
可補助：健身房、運動場館、藝文展演、電影、美術館、全家禮包等。
不可補助：餐飲、運動鞋、Netflix、遊戲點數、圖書等。
報帳需附：發票（含統編）、活動照片、消費清單、存摺影本。
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

    
