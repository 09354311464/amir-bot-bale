import requests
import time
import json

# ===================== تنظیمات =====================
BOT_TOKEN = "1161179518:fDsW1ujcnjivEIAPfPySnWeV8IcmnEtNotKmtERs"
BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}/"
NESHAN_API_KEY = "service.23ed45dcc78e4f9a80bd5eb25cd6b2f5"
DATA_FILE = "routes_data.json"

# ===================== ذخیره مسیر =====================
def save_route(data):
    try:
        old_data = []
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                old_data = json.load(f)
        except FileNotFoundError:
            old_data = []
        old_data.append(data)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(old_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("خطا در ذخیره:", e)

# ===================== ارسال پیام =====================
def send_message(chat_id, text):
    url = BASE_URL + "sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print("خطا در ارسال پیام:", e)

# ===================== اعتبارسنجی مختصات =====================
def valid_coordinate_pair(s):
    try:
        lat, lon = map(float, s.split(","))
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except:
        return False

# ===================== لینک نهایی مسیر‌یابی نشان =====================
def neshn_route_link(origin, destination, vehicle="d"):
    return f"https://nshn.ir/?origin={origin}&destination={destination}&vehicle={vehicle}"

# ===================== درخواست مسیر =====================
def get_route(origin, destination):
    url = f"https://api.neshan.org/v2/direction?origin={origin}&destination={destination}"
    headers = {"Api-Key": NESHAN_API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        if r.status_code != 200 or "routes" not in data or len(data["routes"]) == 0:
            return None
        leg = data["routes"][0]["legs"][0]
        distance = leg["distance"]["text"]
        duration = leg["duration"]["text"]
        return {"distance": distance, "duration": duration, "raw": data}
    except Exception as e:
        print("خطا در دریافت مسیر:", e)
        return None

# ===================== پردازش پیام =====================
def handle_message(text, chat_id):
    if "->" not in text:
        send_message(chat_id, "لطفا مختصات را به شکل زیر ارسال کنید:\n35.6892,51.3890 -> 35.7006,51.3370")
        return

    try:
        origin_raw, destination_raw = map(str.strip, text.split("->", 1))
    except:
        send_message(chat_id, "فرمت اشتباه است. مثال درست:\n35.6892,51.3890 -> 35.7006,51.3370")
        return

    if not (valid_coordinate_pair(origin_raw) and valid_coordinate_pair(destination_raw)):
        send_message(chat_id, "مختصات معتبر نیستند یا خارج از بازهٔ مجاز هستند. فرمت: lat,lon")
        return

    send_message(chat_id, "در حال محاسبه مسیر...")

    res = get_route(origin_raw, destination_raw)
    if not res:
        send_message(chat_id, "خطا در دریافت مسیر از نشان.")
        return

    # ذخیره مسیر
    record = {
        "origin": origin_raw,
        "destination": destination_raw,
        "distance": res["distance"],
        "duration": res["duration"],
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_route(record)

    # لینک نهایی مسیر‌یابی نشان
    link = neshn_route_link(origin_raw, destination_raw)
    msg_text = (
        f"📍 مسیر پیدا شد:\n"
        f"مسافت کل: {res['distance']}\n"
        f"زمان تقریبی: {res['duration']}\n"
        f"برای هدایت به نشان روی لینک زیر کلیک کنید:\n{link}\n\n"
        f"✅ اطلاعات مسیر ذخیره شد."
    )
    send_message(chat_id, msg_text)

# ===================== getUpdates =====================
def get_updates(offset=None):
    url = BASE_URL + "getUpdates"
    params = {}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json()
    except Exception as e:
        print("خطا در getUpdates:", e)
        return {"result": []}

# ===================== حلقه اصلی =====================
def main():
    last_update_id = None
    print("ربات فعال شد...")
    while True:
        updates = get_updates(last_update_id)
        for item in updates.get("result", []):
            last_update_id = item.get("update_id", 0) + 1
            message = item.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")

            if text and chat_id:
                print(f"پیام از {chat_id}: {text}")
                handle_message(text, chat_id)
        time.sleep(1)

if __name__ == "__main__":
    main()
