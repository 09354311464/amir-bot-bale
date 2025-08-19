import requests

# توکن ربات بله
BOT_TOKEN ="1161179518:fDsW1ujcnjivEIAPfPySnWeV8IcmnEtNotKmtERs"
BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}/"

# کلید API نشان
NESHAN_API_KEY = "service.23ed45dcc78e4f9a80bd5eb25cd6b2f5"

# تابع ارسال پیام در بله
def send_message(chat_id, text):
    url = BASE_URL + "sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

# گرفتن آپدیت‌ها از بله
def get_updates():
    url = BASE_URL + "getUpdates"
    resp = requests.get(url)
    return resp.json()

# گرفتن آدرس از API نشان
def get_address(lat, lon):
    url = f"https://api.neshan.org/v5/reverse?lat={lat}&lng={lon}"
    headers = {"Api-Key": NESHAN_API_KEY}
    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        data = resp.json()
        return data.get("formatted_address", "آدرس پیدا نشد ❌")
    else:
        return f"خطا: {resp.status_code} - {resp.text}"

# اجرای ربات
last_update_id = 0
while True:
    updates = get_updates()
    for update in updates.get("result", []):
        update_id = update["update_id"]
        if update_id > last_update_id:
            message = update.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")

            # اگر مختصات داد، آدرس بده
            if "," in text:
                try:
                    lat, lon = map(float, text.split(","))
                    address = get_address(lat, lon)
                    send_message(chat_id, f"📍 آدرس: {address}")
                except:
                    send_message(chat_id, "❌ فرمت مختصات اشتباه است. مثال: 35.6892,51.3890")
            else:
                send_message(chat_id, "سلام! مختصات رو به فرمت `lat,lon` بفرست تا آدرس بدم.")

            last_update_id = update_id
