from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    FlexSendMessage, MessageAction, FollowEvent
)
import requests
import os
import json
from dotenv import load_dotenv

# ✅ 讀取 .env 中的金鑰
load_dotenv()
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ✅ 讀取 FAQ JSON 資料
with open("faq_data.json", encoding="utf-8") as f:
    faq_data = json.load(f)

# ✅ 模糊比對 FAQ 關鍵字
def get_relevant_faq(user_input):
    def search_nested(d):
        for key, value in d.items():
            if key in user_input:
                if isinstance(value, dict):
                    return f"{key}：\n" + "\n".join(
                        [f"{k}：{', '.join(v) if isinstance(v, list) else v}" for k, v in value.items()]
                    )
                else:
                    return f"{key}：{value}"
            elif isinstance(value, dict):
                result = search_nested(value)
                if result:
                    return result
        return None
    return search_nested(faq_data)


# ✅ 活動說明
activity_info = """
你是新北捷運公司的客服機器人，專門回答「CHILL放鬆 全家加碼 FUN 暑假」補助活動問題。
請用親切、簡單的語氣回覆同仁。
如果問題與補助活動無關，請先試著理解內容是否**可能**與補助相關（例如地點、活動名稱）。
如果無法確定，也可以回覆：「這個項目是否能報帳，建議詢問承辦人確認比較保險喔～」
請根據內部 FAQ 資料回覆內容。
⚠️ 回覆請不要使用 Markdown 格式，只使用純文字回覆。

🚫 不可補助項目：
- 餐飲（如星巴克、夜市等）
- 交通與住宿費（高鐵、旅館等）
- 非法或博弈性活動（如彩券、賭場）
- 遊戲點數、線上會員費（如 Netflix、Disney+）
- 商品購買（如運動鞋、圖書）
- ❗ 八大行業（如 KTV、酒店、夜店等）即使與藝文性質有關，依補助規定仍屬排除項目，請依行政分類為準。
"""


# ✅ Gemini 回覆邏輯（插入 FAQ 說明）
def call_gemini_api(user_input):
    faq_hint = get_relevant_faq(user_input)
    prompt = activity_info
    if faq_hint:
        prompt += f"\n\n📌 參考資料：\n{faq_hint}"
    prompt += f"\n\n使用者問題：{user_input}"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        print("🔄 Gemini API 回傳內容：", result)
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

# 加好友時傳 Flex 選單
@handler.add(FollowEvent)
def handle_follow(event):
    send_flex_menu(event)

# 處理一般訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()
    print(f"🗣️ 使用者輸入：{user_input}")

    if user_input.lower() in ["menu", "選單", "我要問問題", "hi", "hello"]:
        print("📤 傳送 Flex 選單")
        send_flex_menu(event)
    else:
        reply_text = call_gemini_api(user_input)
        print(f"🤖 Gemini 回覆：{reply_text}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# 啟動 Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
