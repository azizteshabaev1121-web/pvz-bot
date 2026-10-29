import json
import urllib.parse
import urllib.request

TOKEN = "9006379873:AAFAqMpfyhsk3pPXT53OFs7tHwOue9FsH4o"
ADMIN_CHAT_ID = 8208422375

PVZ_NAMES = {
    "pvz1": "📍 ПВЗ №1 ДУКЕНТ-КАСКАД (14-квартал, дом-6)",
    "pvz2": "📍 ПВЗ №2 УРИКЗОР МАРКЕТ (ул. Ахунбабаева, дом-14/1)",
    "pvz3": "📍 ПВЗ №3 УНИВЕРСИТЕТ (ул. Узбекистон Мустакиллиги, 80)",
    "pvz4": "📍 ПВЗ №4 30-ЛЕТ ЗАМИН-1 (ул. Бунёдкор, дом-210)",
}

TEXTS = {
    "ru": {
        "welcome": (
            "Здравствуйте! Вы обращаетесь по точке: <b>{pvz_title}</b>.\n\nОпишите"
            " вашу проблему или жалобу (можно отправить текст, фото или видео)."
            " Руководство обязательно изучит ваш отзыв."
        ),
        "success": "✅ Спасибо! Ваше обращение успешно отправлено руководителю.",
        "admin_new": (
            "⚠️ <b>Новая жалоба от клиента!</b>\n\n{pvz_title}\n👤"
            " <b>Клиент:</b> {username}\n"
        ),
    },
    "uz": {
        "welcome": (
            "Assalomu alaykum! Siz murojaat qilayotgan punkt:"
            " <b>{pvz_title}</b>.\n\nMuammo yoki shikoyatingizni yozib"
            " qoldiring (matn, rasm yoki video yuborishingiz mumkin)."
            " Rahbariyat albatta murojaatingizni ko'rib chiqadi."
        ),
        "success": (
            "✅ Rahmat! Murojaatingiz rahbariyatga muvaffaqiyatli yuborildi."
        ),
        "admin_new": (
            "⚠️ <b>Mijozdan yangi shikoyat!</b>\n\n{pvz_title}\n👤"
            " <b>Mijoz:</b> {username}\n"
        ),
    },
}

user_pvz = {}
user_langs = {}
user_states = {}


def send_message(chat_id, text, reply_markup=None):
  url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
  data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
  if reply_markup:
    data["reply_markup"] = json.dumps(reply_markup)
  req = urllib.request.Request(
      url,
      data=urllib.parse.urlencode(data).encode("utf-8"),
      headers={"User-Agent": "Mozilla/5.0"},
  )
  try:
    with urllib.request.urlopen(req) as response:
      return json.loads(response.read().decode("utf-8"))
  except Exception as e:
    print("Error sending message:", e)


def forward_message(chat_id, from_chat_id, message_id):
  url = f"https://api.telegram.org/bot{TOKEN}/forwardMessage"
  data = {
      "chat_id": chat_id,
      "from_chat_id": from_chat_id,
      "message_id": message_id,
  }
  req = urllib.request.Request(
      url,
      data=urllib.parse.urlencode(data).encode("utf-8"),
      headers={"User-Agent": "Mozilla/5.0"},
  )
  try:
    with urllib.request.urlopen(req) as response:
      return json.loads(response.read().decode("utf-8"))
  except Exception as e:
    print("Error forwarding message:", e)


def answer_callback_query(callback_query_id):
  url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
  data = {"callback_query_id": callback_query_id}
  req = urllib.request.Request(
      url,
      data=urllib.parse.urlencode(data).encode("utf-8"),
      headers={"User-Agent": "Mozilla/5.0"},
  )
  try:
    with urllib.request.urlopen(req) as response:
      return json.loads(response.read().decode("utf-8"))
  except Exception as e:
    print("Error answering callback:", e)


def delete_webhook():
  """Сбрасывает вебхук, чтобы работал режим getUpdates"""
  url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook?drop_pending_updates=true"
  try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
      print("Вебхук успешно сброшен:", response.read().decode("utf-8"))
  except Exception as e:
    print("Ошибка сброса вебхука:", e)


def main():
  # Сбрасываем старый вебхук при запуске
  delete_webhook()
  print("Бот успешно запущен и ждет жалобы...")

  offset = 0
  while True:
    url = (
        f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=30"
    )
    try:
      req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
      with urllib.request.urlopen(req, timeout=35) as response:
        result = json.loads(response.read().decode("utf-8"))
        if result.get("ok"):
          for update in result.get("result", []):
            offset = update["update_id"] + 1

            if "callback_query" in update:
              cq = update["callback_query"]
              cq_id = cq["id"]
              user = cq["from"]
              user_id = user["id"]
              data = cq["data"]
              chat_id = cq["message"]["chat"]["id"]

              answer_callback_query(cq_id)

              if data in ["lang_ru", "lang_uz"]:
                lang = "ru" if data == "lang_ru" else "uz"
                user_langs[user_id] = lang
                user_states[user_id] = "waiting_for_complaint"

                pvz_title = user_pvz.get(user_id, "📍 ПВЗ (Точка)")
                text = TEXTS[lang]["welcome"].format(pvz_title=pvz_title)
                send_message(chat_id, text)
              continue

            message = update.get("message")
            if not message:
              continue

            chat_id = message["chat"]["id"]
            text = message.get("text", "")
            user = message["from"]
            user_id = user["id"]
            username = (
                f"@{user.get('username')}"
                if user.get("username")
                else f"ID: {user_id} ({user.get('first_name', '')})"
            )

            if text.startswith("/start"):
              parts = text.split(maxsplit=1)
              pvz_code = parts[1] if len(parts) > 1 else "unknown"
              pvz_title = PVZ_NAMES.get(pvz_code, "📍 ПВЗ (Точка)")
              user_pvz[user_id] = pvz_title

              keyboard = {
                  "inline_keyboard": [[
                      {"text": "🇷🇺 Русский", "callback_data": "lang_ru"},
                      {"text": "🇺🇿 O'zbekcha", "callback_data": "lang_uz"},
                  ]]
              }
              send_message(
                  chat_id,
                  "Пожалуйста, выберите язык:\nIltimos, tilni tanlang:",
                  reply_markup=keyboard,
              )
            else:
              lang = user_langs.get(user_id, "ru")
              pvz_title = user_pvz.get(user_id, "📍 ПВЗ (Точка)")

              admin_text = TEXTS[lang]["admin_new"].format(
                  pvz_title=pvz_title, username=username
              )
              send_message(ADMIN_CHAT_ID, admin_text)
              forward_message(ADMIN_CHAT_ID, chat_id, message["message_id"])

              send_message(chat_id, TEXTS[lang]["success"])
              user_states.pop(user_id, None)
    except Exception as e:
      print("Polling error:", e)


if __name__ == "__main__":
  main()