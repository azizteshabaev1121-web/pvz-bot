import os
from threading import Thread
from flask import Flask
import telebot
from telebot import types

# Данные бота и администратора
TOKEN = '9006379873:AAFAqMpfyhsk3pPXT53OFs7tHwOue9FsH4o'
ADMIN_CHAT_ID = '8208422375'

bot = telebot.TeleBot(TOKEN)

# Словарь для хранения выбранного языка и состояния пользователей
user_lang = {}
user_pvz = {}

# Тексты на двух языках
TEXTS = {
    'ru': {
        'choose_lang': 'Пожалуйста, выберите язык / Tilni tanlang:',
        'choose_pvz': 'Выберите ваш ПВЗ (Точку):',
        'pvz_1': '📍 ПВЗ Аhangaran',
        'pvz_2': '📍 ПВЗ Angren',
        'welcome_complaint': (
            'Здравствуйте! Вы обращаетесь по точке: {pvz}.\n\nОпишите вашу проблему'
            ' или жалобу (можно отправить текст, фото или видео). Руководство'
            ' обязательно изучит ваш отзыв.'
        ),
        'success': 'Ваша жалоба успешно отправлена руководству. Спасибо!',
    },
    'uz': {
        'choose_lang': 'Iltimos, tilni tanlang / Пожалуйста, выберите язык:',
        'choose_pvz': 'O‘zingizning ПВЗ (Nuqtangizni) tanlang:',
        'pvz_1': '📍 ПВЗ Аhangaran',
        'pvz_2': '📍 ПВЗ Angren',
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


# 1. Веб-сервер Flask для Render (чтобы хостинг видел открытый порт)
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


# 2. Логика Telegram-бота
@bot.message_handler(commands=['start'])
def send_welcome(message):
  markup = types.InlineKeyboardMarkup(row_width=2)
  btn_ru = types.InlineKeyboardButton('🇷🇺 Русский', callback_data='lang_ru')
  btn_uz = types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data='lang_uz')
  markup.add(btn_ru, btn_uz)

  bot.send_message(
      message.chat.id,
      'Здравствуйте! Пожалуйста, выберите язык / Tilni tanlang:',
      reply_markup=markup,
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
  chat_id = call.message.chat.id
  lang = call.data.split('_')[1]
  user_lang[chat_id] = lang

  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
  if lang == 'ru':
    markup.add(
        types.KeyboardButton(TEXTS['ru']['pvz_1']),
        types.KeyboardButton(TEXTS['ru']['pvz_2']),
    )
    text = TEXTS['ru']['choose_pvz']
  else:
    markup.add(
        types.KeyboardButton(TEXTS['uz']['pvz_1']),
        types.KeyboardButton(TEXTS['uz']['pvz_2']),
    )
    text = TEXTS['uz']['choose_pvz']

  bot.send_message(chat_id, text, reply_markup=markup)


@bot.message_handler(
    func=lambda message: message.text
    in [TEXTS['ru']['pvz_1'], TEXTS['ru']['pvz_2'], TEXTS['uz']['pvz_1'], TEXTS['uz']['pvz_2']]
)
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
  lang = user_lang.get(chat_id, 'ru')
  pvz = user_pvz.get(chat_id, 'ПВЗ (Точка)')

  # Отправляем подтверждение пользователю
  bot.reply_to(message, TEXTS[lang]['success'])

  # Пересылаем жалобу администратору
  admin_text = (
      f'📩 **Новая жалоба!**\nПВЗ: {pvz}\nОт: @{message.from_user.username or message.from_user.first_name} (ID: {chat_id})'
  )
  bot.send_message(ADMIN_CHAT_ID, admin_text, parse_mode='Markdown')
  bot.forward_message(ADMIN_CHAT_ID, chat_id, message.message_id)


# 3. Запуск веб-сервера и бота
if __name__ == '__main__':
  keep_alive()  # Запускаем Flask для Render
  print('Бот запущен в облаке...')
  bot.infinity_polling()
