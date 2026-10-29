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

TEXTS = {
    'ru': {
        'choose_pvz': 'Выберите ваш ПВЗ (Точку):',
        'pvz_1': '📍 ПВЗ Аhangaran',
        'pvz_2': '📍 ПВЗ Angren',
        'welcome_complaint': 'Здравствуйте! Вы обращаетесь по точке: {pvz}.\n\nОпишите вашу проблему или жалобу (можно отправить текст, фото или видео). Руководство обязательно изучит ваш отзыв.',
        'success': 'Ваша жалоба успешно отправлена руководству. Спасибо!'
    },
    'uz': {
        'choose_pvz': 'O‘zingizning ПВЗ (Nuqtangizni) tanlang:',
        'pvz_1': '📍 ПВЗ Аhangaran',
        'pvz_2': '📍 ПВЗ Angren',
        'welcome_complaint': "Assalomu alaykum! Siz murojaat qilayotgan punkt: {pvz}.\n\nMuammo yoki shikoyatingizni yozib qoldiring (matn, rasm yoki video yuborishingiz mumkin). Rahbariyat albatta ko‘rib chiqadi.",
        'success': "Shikoyatingiz rahbariyatga muvaffaqiyatli yuborildi. Rahmat!"
    }
}

# Веб-сервер Flask для Render
app = Flask('')

@app.route('/')
def home():
    return "PVZ Bot is active and running 24/7!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Команда /start с полным сбросом памяти
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_lang.pop(chat_id, None)
    user_pvz.pop(chat_id, None)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_ru = types.InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')
    btn_uz = types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data='lang_uz')
    markup.add(btn_ru, btn_uz)
    
    bot.send_message(chat_id, "Здравствуйте! Пожалуйста, выберите язык / Tilni tanlang:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    chat_id = call.message.chat.id
    lang = call.data.split('_')[1]
    user_lang[chat_id] = lang
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if lang == 'ru':
        markup.add(types.KeyboardButton(TEXTS['ru']['pvz_1']), types.KeyboardButton(TEXTS['ru']['pvz_2']))
        text = TEXTS['ru']['choose_pvz']
    else:
        markup.add(types.KeyboardButton(TEXTS['uz']['pvz_1']), types.KeyboardButton(TEXTS['uz']['pvz_2']))
        text = TEXTS['uz']['choose_pvz']
        
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in [TEXTS['ru']['pvz_1'], TEXTS['ru']['pvz_2'], TEXTS['uz']['pvz_1'], TEXTS['uz']['pvz_2']])
def set_pvz(message):
    chat_id = message.chat.id
    lang = user_lang.get(chat_id, 'ru')
    user_pvz[chat_id] = message.text
    
    text = TEXTS[lang]['welcome_complaint'].format(pvz=message.text)
    bot.send_message(chat_id, text, reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio'])
def handle_complaint(message):
    chat_id = message.chat.id
    
    # Если пользователь пишет текст до выбора языка/точки, возвращаем к /start
    if chat_id not in user_lang or chat_id not in user_pvz:
        bot.send_message(chat_id, "Пожалуйста, нажмите /start для начала работы с ботом.")
        return

    lang = user_lang.get(chat_id, 'ru')
    pvz = user_pvz.get(chat_id, 'ПВЗ (Точка)')
    
    bot.reply_to(message, TEXTS[lang]['success'])
    
    admin_text = f"📩 **Новая жалоба!**\nПВЗ: {pvz}\nОт: @{message.from_user.username or message.from_user.first_name} (ID: {chat_id})"
    bot.send_message(ADMIN_CHAT_ID, admin_text, parse_mode='Markdown')
    bot.forward_message(ADMIN_CHAT_ID, chat_id, message.message_id)

if __name__ == '__main__':
    keep_alive()
    print("Бот запущен в облаке...")
    bot.infinity_polling(skip_pending=True)
