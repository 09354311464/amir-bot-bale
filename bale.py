import requests
import time
import json

BOT_TOKEN = "1161179518:fDsW1ujcnjivEIAPfPySnWeV8IcmnEtNotKmtERs"
BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}/"
NESHAN_API_KEY = "service.23ed45dcc78e4f9a80bd5eb25cd6b2f5"

DESTINATIONS = {
    "برج میلاد": "35.745,51.330",
    "میدان آزادی": "35.699,51.337"
}

user_origin_map = {}  # نگهداری مبدا کاربران

# ====== ارسال پیام ساده ======
def send_message(chat_id, text, keyboard=None):
    url = BASE_URL + "sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if keyboard:
        data["keyboard"] = keyboard
    try:
        r = requests.post(url, json=data, timeout=10)
        return r.json()
    except Exception as e:
        print("خطا در ارسال پیام:", e)
        return None

# ====== لینک نِشان ======
def neshan_link_with_fields(origin, destination):
    olat, olng = map(str.strip, origin.split(","))
    dlat, dlng = map(str.strip, destination.split(","))
    return f"https://map.neshan.org/maps/routing/car?originLat={olat}&originLng={olng}&destinationLat={dlat}&destinationLng={dlng}&travelMode=car&zoom=13"

# ====== درخواست مسیر ======
def get_route(origin, destination):
    url = f"https://api.neshan.org/v2/direction?origin={origin}&destination={destination}"
    headers = {"Api-Key": NESHAN_API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
    except Exception as e:
        return {"ok": False, "error": f"خطا در ارتباط با Neshan: {e}"}

    if r.status_code != 200 or "routes" not in data or len(data["routes"]) == 0:
        return {"ok": False, "error": "هیچ مسیری پیدا نشد."}

    route = data["routes"][0]
    leg = route.get("legs", [])[0]
    distance = leg.get("distance", {}).get("text", "")
    duration = leg.get("duration", {}).get("text", "")
    steps = leg.get("steps", [])
    return {"ok": True, "distance": distance, "duration": duration, "steps": steps}

# ====== پردازش مسیر و ارسال مراحل ======
def handle_destination_choice(origin, choice, chat_id):
    destination = DESTINATIONS.get(choice)
    if not destination:
        send_message(chat_id, "گزینه مقصد نامعتبر است.")
        return

    send_message(chat_id, "در حال محاسبه مسیر...")
    res = get_route(origin, destination)
    if not res["ok"]:
        send_message(chat_id, f"خطا: {res['error']}")
        return

    link = neshan_link_with_fields(origin, destination)
    intro = f"مسیر پیدا شد:\nمسافت کل: {res['distance']}\nمدت زمان کل: {res['duration']}\n\nلینک مسیر:\n{link}"
    send_message(chat_id, intro)

    # ارسال مراحل مسیر
    steps = res["steps"]
    if not steps:
        send_message(chat_id, "مراحل مسیر خالی است.")
        return
    chunk_size = 8
    for i in range(0, len(steps), chunk_size):
        chunk = steps[i:i+chunk_size]
        lines = []
        for idx, step in enumerate(chunk, start=i+1):
            instr = step.get("instruction", "").replace("\n", " ").strip()
            dist = step.get("distance", {}).get("text", "")
            dur = step.get("duration", {}).get("text", "")
            if not instr:
                instr = step.get("name", "حرکت")
            if len(instr) > 300:
                instr = instr[:300] + "..."
            lines.append(f"{idx}. {instr} ({dist}, {dur})")
        send_message(chat_id, "\n".join(lines))

# ====== getUpdates ======
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

# ====== اجرای ربات ======
def main():
    last_update_id = None
    print("ربات شروع به کار کرد...")
    while True:
        updates = get_updates(last_update_id)
        for item in updates.get("result", []):
            last_update_id = item.get("update_id", 0) + 1
            message = item.get("message", {})
            chat = message.get("chat", {})
            chat_id = chat.get("id")
            text = message.get("text", "")
            location = message.get("location", {})

            # ---- /start ----
            if text == "/start" and chat_id:
                if chat_id in user_origin_map:
                    del user_origin_map[chat_id]  # پاک کردن مبدا قبلی
                send_message(chat_id, "لطفا موقعیت خود را ارسال کنید تا مسیر به مقصد انتخابی نشان داده شود.")
                continue

            # ---- موقعیت کاربر ----
            if location and chat_id:
                lat = location.get("latitude")
                lon = location.get("longitude")
                if lat and lon:
                    user_origin_map[chat_id] = f"{lat},{lon}"
                    keyboard = {
                        "type": "reply",
                        "buttons": [
                            ["برج میلاد"],
                            ["میدان آزادی"]
                        ]
                    }
                    send_message(chat_id, "لطفا مقصد را انتخاب کنید:", keyboard=keyboard)
                continue

            # ---- انتخاب مقصد ----
            if text in DESTINATIONS and chat_id in user_origin_map:
                origin = user_origin_map[chat_id]
                handle_destination_choice(origin, text, chat_id)
                del user_origin_map[chat_id]
                continue

            # ---- متن نامربوط ----
            if text and chat_id:
                send_message(chat_id, "لطفا موقعیت خود را ارسال کنید تا مسیر به مقصد انتخابی نشان داده شود.")

        time.sleep(1)

if __name__ == "__main__":
    main()
