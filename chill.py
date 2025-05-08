from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, MessageAction, FollowEvent
)
import requests
import os
from dotenv import load_dotenv

# ✅ 讀取 .env 中的金鑰
load_dotenv()
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 活動說明與限制（已去除 **，允許表情符號）
activity_info = """
你是新北捷運的客服機器人，負責回答 114 年「CHILL放鬆 全家加碼 FUN暑假」補助活動的問題。請使用親切、簡單的語氣回應員工。

✅ 回覆時可以使用表情符號（例如 ✅ 📌 📷 等），但請不要使用任何 Markdown 格式（如 **加粗符號** 或 `反引號`）。

📌 活動摘要：
- 活動期間：114年6月1日～11月30日，限每月當月實報實銷
- 補助金額：每人上限 3,000 元
- 對象：公司正式員工（員編 M 開頭，工讀生/外派不可）
- 檢附文件：需附發票或票券（含統編）、活動照片、消費明細、存摺影本
- 僅限國內收據/票券，若為門票須附活動照片

🎯 可補助範圍：
- 國民運動中心、健身房、場租（羽球等）、賽事門票
- 展覽、戲劇、演唱會、電影院、美術館
- 全家十四張店的「FUN暑假大禮包」（整組）

🚫 不可補助項目：
- 餐飲（星巴克、路易莎等）、商品（運動鞋）、遊戲點數
- 線上娛樂（Netflix 等）、交通費、紀念品店如非官方開立
- 無金額票券無法報帳，需有佐證

📷 若收據無明細，請補活動照片
🎁 FUN禮包享 50% 回饋，限十四張門市使用
"""

# Gemini 回覆邏輯
def call_gemini_api(user_input):
    prompt = f"{activity_info}\n\n使用者問題：{user_input}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("❌ 發生錯誤：", e)
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
    line_bot_api.reply_message(event.reply_token, flex_message)

# Webhook 路由
@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_data(as_text=True)
    signature = request.headers['X-Line-Signature']
    handler.handle(body, signature)
    return 'OK'

# 加好友時觸發 Flex 選單
@handler.add(FollowEvent)
def handle_follow(event):
    send_flex_menu(event)

# 一般訊息處理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()
    if user_input.lower() in ["menu", "選單", "我要問問題", "hi", "hello"]:
        send_flex_menu(event)
    else:
        reply_text = call_gemini_api(user_input)
        print(f"🗣️ 使用者：{user_input}")
        print(f"🤖 回覆：{reply_text}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# Flask 本機啟動（Render 上會自動執行）
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
