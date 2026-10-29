import os
from threading import Thread
from flask import Flask
import telebot

# Ваши данные бота и администратора
TOKEN = '9006379873:AAFAqMpfyhsk3pPXT53OFs7tHwOue9FsH4o'
ADMIN_CHAT_ID = '8208422375'

bot = telebot.TeleBot(TOKEN)

# 1. Настройка веб-сервера Flask (нужен для Render, чтобы открыть порт)
app = Flask('')


@app.route('/')
def home():
  return 'Bot is active and running 24/7!'


def run():
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)


def keep_alive():
  t = Thread(target=run)
  t.start()


# 2. Обработчики сообщений бота
@bot.message_handler(commands=['start'])
def send_welcome(message):
  bot.reply_to(
      message, 'Здравствуйте! ПВЗ бот успешно запущен и работает в штатном режиме.'
  )


@bot.message_handler(func=lambda message: True)
def echo_all(message):
  # Пересылка сообщения администратору при необходимости или стандартный ответ
  bot.reply_to(
      message, 'Ваше сообщение принято! Скоро с вами свяжутся сотрудники ПВЗ.'
  )


# 3. Главный запуск программы
if __name__ == '__main__':
  # Сначала запускаем веб-сервер в фоне (чтобы Render видел открытый порт)
  keep_alive()

  # Затем запускаем самого Telegram-бота
  print('Бот запущен и слушает сообщения...')
  bot.infinity_polling()
