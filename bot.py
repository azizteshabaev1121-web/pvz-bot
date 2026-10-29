import os
from threading import Thread
from flask import Flask
import telebot
from telebot import types

TOKEN = '9006379873:AAFAqMpfyhsk3pPXT53OFs7tHwOue9FsH4o'
ADMIN_CHAT_ID = '8208422375'

bot = telebot.TeleBot(TOKEN)

user_lang = {}
user_pvz = {}

# Ваши 4 точки ПВЗ с адресами
PVZ_NAMES = {
    'pvz1': '📍 ПВЗ №1 ДУКЕНТ-КАСКАД (14-квартал, дом-6)',
    'pvz2': '📍 ПВЗ №2 УРИКЗОР МАРКЕТ (ул. Ахунбабаева, дом-14/1)',
    'pvz3': '📍 ПВЗ №3 УНИВЕРСИТЕТ (ул. Узбекистон Мустакиллиги, 80)',
    'pvz4': '📍 ПВЗ №4 30-ЛЕТ ЗАМИН-1 (ул. Бунёдкор, дом-210)',
}

TEXTS = {
    'ru': {
        'welcome_complaint': (
            'Здравствуйте! Вы обращаетесь по точке: {pvz}.\n\nОпишите вашу проблему'
            ' или жалобу (можно отправить текст, фото или видео). Руководство'
            ' обязательно изучит ваш отзыв.'
        ),
        'success': 'Ваша жалоба успешно отправлена руководству. Спасибо!',
    },
    'uz': {
        'welcome_complaint': (
            "Assalomu alaykum! Siz murojaat qilayotgan punkt: {pvz}.\n\nMuammo"
            " yoki shikoyatingizni yozib qoldiring (matn, rasm yoki video"
            ' yuborishingiz mumkin). Rahbariyat albatta ko‘rib chiqadi.'
        ),
        'success': (
            " Shikoyatingiz rahbariyatga muvaffaqiyatli yuborildi. Rahmat!"
        ),
    },
}

app = Flask('')


@app.route('/')
def home():
  return 'PVZ Bot is active and running 24/7!'


def run():
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)


def keep_alive():
  t = Thread(target=run)
  t.start()


# Умный перехват любых параметров из QR-кодов (старых и новых)
@bot.message_handler(commands=['start'])
def send_welcome(message):
  chat_id = message.chat.id
  user_lang.pop(chat_id, None)
  user_pvz.pop(chat_id, None)

  args = message.text.split()
  if len(args) > 1:
    param = args[1].lower()
    # Ловим любые варианты, зашитые в ваши QR-коды
    if '1' in param or 'dukent' in param or 'pvz1' in param:
      user_pvz[chat_id] = PVZ_NAMES['pvz1']
    elif '2' in param or 'urikzor' in param or 'pvz2' in param:
      user_pvz[chat_id] = PVZ_NAMES['pvz2']
    elif '3' in param or 'universitet' in param or 'pvz3' in param:
      user_pvz[chat_id] = PVZ_NAMES['pvz3']
    elif (
        '4' in param
        or 'zamin' in param
        or 'bunyodkor' in param
        or 'angren' in param
        or 'pvz4' in param
    ):
      user_pvz[chat_id] = PVZ_NAMES['pvz4']

  markup = types.InlineKeyboardMarkup(row_width=2)
  btn_ru = types.InlineKeyboardButton('🇷🇺 Русский', callback_data='lang_ru')
  btn_uz = types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data='lang_uz')
  markup.add(btn_ru, btn_uz)

  bot.send_message(
      chat_id,
      'Здравствуйте! Пожалуйста, выберите язык / Tilni tanlang:',
      reply_markup=markup,
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
  chat_id = call.message.chat.id
  lang = call.data.split('_')[1]
  user_lang[chat_id] = lang

  if chat_id in user_pvz:
    pvz = user_pvz[chat_id]
    text = TEXTS[lang]['welcome_complaint'].format(pvz=pvz)
    bot.edit_message_text(
        text=text,
        chat_id=chat_id,
        message_id=call.message.message_id,
        reply_markup=None,
    )
  else:
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True
    )
    for name in PVZ_NAMES.values():
      markup.add(types.KeyboardButton(name))
    bot.send_message(
        chat_id,
        'Выберите ваш ПВЗ (Точку) / Punktni tanlang:',
        reply_markup=markup,
    )


@bot.message_handler(func=lambda message: message.text in PVZ_NAMES.values())
def set_pvz(message):
  chat_id = message.chat.id
  lang = user_lang.get(chat_id, 'ru')
  user_pvz[chat_id] = message.text

  text = TEXTS[lang]['welcome_complaint'].format(pvz=message.text)
  bot.send_message(chat_id, text, reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(
    content_types=['text', 'photo', 'video', 'document', 'audio']
)
def handle_complaint(message):
  chat_id = message.chat.id

  if chat_id not in user_lang or chat_id not in user_pvz:
    bot.send_message(
        chat_id,
        'Пожалуйста, отсканируйте QR-код точки или перейдите по ссылке /start.',
    )
    return

  lang = user_lang.get(chat_id, 'ru')
  pvz = user_pvz.get(chat_id, 'ПВЗ (Точка)')

  bot.reply_to(message, TEXTS[lang]['success'])

  admin_text = (
      f'📩 **Новая жалоба!**\nПВЗ: {pvz}\nОт: @{message.from_user.username or message.from_user.first_name} (ID: {chat_id})'
  )
  bot.send_message(ADMIN_CHAT_ID, admin_text, parse_mode='Markdown')
  bot.forward_message(ADMIN_CHAT_ID, chat_id, message.message_id)


if __name__ == '__main__':
  keep_alive()
  print('Бот запущен в облаке...')
  bot.infinity_polling(skip_pending=True)
