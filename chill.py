from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FollowEvent, FlexSendMessage
import requests
import os
import json
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, util

# ✅ 載入 .env
load_dotenv()
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ✅ 初始化 Flask 與 LINE API
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ✅ 載入 FAQ JSON 並扁平化處理
with open("faq_data.json", encoding="utf-8") as f:
    raw_data = json.load(f)

flattened_faq_dict = {}
for section in raw_data:
    for q, a in raw_data[section].items():
        flattened_faq_dict[q] = a

# ✅ 初始化句向量模型
model = SentenceTransformer('distiluse-base-multilingual-cased')
faq_keys = list(flattened_faq_dict.keys())
faq_embeddings = model.encode(faq_keys, convert_to_tensor=True)

def get_relevant_faq(user_input):
    input_embedding = model.encode(user_input, convert_to_tensor=True)
    cos_scores = util.cos_sim(input_embedding, faq_embeddings)[0]
    top_idx = cos_scores.argmax().item()
    most_similar_q = faq_keys[top_idx]
    answer = flattened_faq_dict[most_similar_q]
    return f"{most_similar_q}：{answer}"


# ✅ 活動說明
activity_info = """
你是新北捷運公司的客服機器人🤖，專門回答「CHILL放鬆 全家加碼 FUN 暑假」補助活動問題💡。
如果問題與補助活動無關，請先試著理解內容是否**可能**與補助相關（例如地點、活動名稱）。
如果無法確定建議詢問承辦人確認比較保險
請根據內部 FAQ 資料回覆內容。
⚠️ 回覆請不要使用 Markdown 格式，只使用純文字回覆。
若使用者問題與 FAQ 中的某題語意相近，請主動選用對應 FAQ 內容來回答。
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
