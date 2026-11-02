import os
import time
import threading
import re
from threading import Thread
from flask import Flask
import telebot
from telebot import types
import requests

TOKEN = '9006379873:AAFAqMpfyhsk3pPXT53OFs7tHwOue9FsH4o'
ADMIN_CHAT_ID = '8208422375'
GOOGLE_SHEET_WEB_APP_URL = 'https://script.google.com/macros/s/AKfycbzQKLZvDOIOFLlcrtUjCt9jhLPf2DSkWOKgHyHb28HzASM8-8KkIYtN8DamLQVi57XejA/exec'

bot = telebot.TeleBot(TOKEN)

user_lang = {}
user_pvz_key = {}
user_action = {}
user_category = {}
user_media_buffer = {}  
user_timers = {}        
dialogue_timers = {}    
admin_message_mapping = {}
active_dialogue = {}    

buffer_lock = threading.Lock()  

MAX_FILES_LIMIT = 10                    
MAX_FILE_SIZE_MB = 20                    
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  
MAX_MAPPING_SIZE = 500                    
DIALOGUE_TIMEOUT = 1800                 # Время жизни активного диалога (30 минут в секундах)

def add_to_mapping(msg_id, client_id):
    with buffer_lock:
        admin_message_mapping[msg_id] = client_id
        if len(admin_message_mapping) > MAX_MAPPING_SIZE:
            oldest_key = next(iter(admin_message_mapping))
            admin_message_mapping.pop(oldest_key, None)

def close_dialogue(chat_id):
    with buffer_lock:
        if active_dialogue.get(chat_id):
            active_dialogue.pop(chat_id, None)
            if chat_id in dialogue_timers:
                dialogue_timers.pop(chat_id, None)
            try:
                bot.send_message(
                    chat_id, 
                    "⏳ Время сеанса связи по этому обращению истекло. Чтобы начать новое обращение, пожалуйста, нажмите /start."
                )
            except Exception:
                pass

PINNED_TEMPLATES_TEXT = (
    "📋 **ШАБЛОНЫ ОТВЕТОВ КЛИЕНТАМ**\n"
    "(Нажмите на нужный текст, чтобы скопировать, отредактируйте и ответьте клиенту):\n\n"
    "1️⃣ **В работу (Русский):**\n"
    "`Здравствуйте! Спасибо за обращение. Мы уже начали разбирать эту ситуацию с сотрудниками точки.`\n\n"
    "2️⃣ **В работу (Узбекский):**\n"
    "`Assalomu alaykum! Murojaatingiz uchun rahmat. Biz hozirda bu holatni punkt xodimlari bilan birgalikda o‘rganib chiqyapmiz.`\n\n"
    "3️⃣ **Уточнить детали (Русский):**\n"
    "`Здравствуйте! Чтобы мы могли точнее во всем разобраться, подскажите, пожалуйста, точную дату, примерное время визита или номер заказа.`\n\n"
    "4️⃣ **Уточнить детали (Узбекский):**\n"
    "`Assalomu alaykum! Vaziyatni aniqroq o‘rganib chiqishimiz uchun, iltimos, tashrif sanasi, taxminiy vaqt yoki buyurtma raqamini yozib yuboring.`\n\n"
    "5️⃣ **Решено / Извинения (Русский):**\n"
    "`Здравствуйте! Спасибо, что сообщили. Мы устранили проблему и провели работу с персоналом. Приносим извинения!`\n\n"
    "6️⃣ **Решено / Извинения (Узбекский):**\n"
    "`Assalomu alaykum! Xabar berganingiz uchun rahmat. Muammoni bartaraf etdik, xodimlar bilan ish olib bordik. Uzr so‘raymiz!`\n\n"
    "7️⃣ **Благодарность (Русский):**\n"
    "`Здравствуйте! Большое спасибо за теплые слова и высокую оценку! Обязательно передадим вашу благодарность сотруднику.`\n\n"
    "8️⃣ **Благодарность (Узбекский):**\n"
    "`Assalomu alaykum! Iliq so‘zlaringiz uchun katta rahmat! Minnatdorchiligingizni xodimimizga yetkazamiz.`\n\n"
    "9️⃣ **Другой ПВЗ / Не наша точка (Русский):**\n"
    "`Здравствуйте! К сожалению, этот бот принимает обращения только по нашим точкам. Ваша проблема относится к другому пункту выдачи. Пожалуйста, обратитесь в официальную службу поддержки в приложении Uzum Market.`\n\n"
    "🔟 **Другой ПВЗ / Не наша точка (Узбекский):**\n"
    "`Assalomu alaykum! Afsuski, ushbu bot faqat bizning punktlar bo‘yicha murojaatlarni qabul qiladi. Sizning murojaatingiz boshqa punktga tegishli. Iltimos, rasmiy Uzum Market ilovasidagi qo‘llab-quvvatlash xizmatiga murojaat qiling.`"
)

PVZ_NAMES_RU = {
    'pvz1': '📍 ПВЗ №1 ДУКЕНТ-КАСКАД (14-квартал, дом-6)',
    'pvz2': '📍 ПВЗ №2 УРИКЗОР_МАРКЕТ (ул. Ахунбабаева, дом-14/1)',
    'pvz3': '📍 ПВЗ №3 УНИВЕРСИТЕТ (ул. Узбекистон Мустакиллиги, дом-80)',
    'pvz4': '📍 ПВЗ №4 30-ЛЕТ_ЗАМИН-1 (ул. Бунёдкор, дом-210)',
}

PVZ_NAMES_UZ = {
    'pvz1': '📍 BTP №1 DUKENT-KASKAD (14-kvartal, 6-uy)',
    'pvz2': '📍 BTP №2 O‘RIKZOR_MARKET (Oxunboboyev ko‘chasi, 14/1-uy)',
    'pvz3': '📍 BTP №3 UNIVERSITET (O‘zbekiston Mustaqilligi ko‘chasi, 80-uy)',
    'pvz4': '📍 BTP №4 30-YIL ZAMIN-1 (Bunyodkor ko‘chasi, 210-uy)',
}

TEXTS = {
    'ru': {
        'choose_action': 'Пожалуйста, выберите цель вашего обращения:',
        'btn_complaint': '📩 Обращение к руководству ПВЗ',
        'btn_praise': '⭐️ Поблагодарить сотрудника',
        'choose_category': 'Выберите категорию вопроса:',
        'cat_1': '🗣 Грубость / Хамство персонала',
        'cat_2': '⏳ Очередь / Медленное обслуживание',
        'cat_3': '📦 Ошибка при выдаче заказа',
        'cat_4': '🧹 Чистота / Порядок в помещении',
        'cat_5': '📝 Другой вопрос или предложение',
        'welcome_complaint': (
            'Категория: {cat}\n'
            'Точка: {pvz}\n\n'
            'Опишите детали вашего обращения.\n'
            f'📌 Можно отправить до {MAX_FILES_LIMIT} файлов (каждый до {MAX_FILE_SIZE_MB} МБ). Бот подождет и отправит всё автоматически.'
        ),
        'welcome_praise': (
            'Вы выбрали: Поблагодарить сотрудника (точка: {pvz}).\n\n'
            'Напишите ваши слова благодарности или отправьте фото/видео.'
        ),
        'success_complaint': '✅ Ваше обращение успешно направлено руководству ПВЗ. Спасибо за помощь в улучшении сервиса!',
        'success_praise': '✅ Ваша благодарность успешно передана руководству! Большое спасибо за теплые слова!',
    },
    'uz': {
        'choose_action': 'Murojaatingiz maqsadini tanlang:',
        'btn_complaint': '📩 BTP rahbariyatiga murojaat',
        'btn_praise': '⭐️ Xodimga minnatdorchilik bildirish',
        'choose_category': 'Mavzu turini tanlang:',
        'cat_1': "🗣 Xodimning qo'pol muomalasi",
        'cat_2': '⏳ Sekin xizmat / Navbat',
        'cat_3': '📦 Buyurtmadagi xatolik',
        'cat_4': '🧹 Xona tozaligi / Tartib',
        'cat_5': '📝 Boshqa taklif yoki savol',
        'welcome_complaint': (
            'Kategoriya: {cat}\n'
            'Punkt: {pvz}\n\n'
            'Murojaatingiz tafsilotlarini yozib qoldiring.\n'
            f'📌 Ko‘pi bilan {MAX_FILES_LIMIT} ta fayl (har biri {MAX_FILE_SIZE_MB} MB gacha) yuborishingiz mumkin. Bot kutib, avtomatik yuboradi.'
        ),
        'welcome_praise': (
            'Siz tanladingiz: Xodimga minnatdorchilik bildirish (punkt: {pvz}).\n\n'
            'Minnatdorchilik so‘zlaringizni yoki rasmlarni yuboring.'
        ),
        'success_complaint': '✅ Murojaatingiz BTP rahbariyatiga muvaffaqiyatli yuborildi. Xizmat sifatini yaxshilashga yordam berganingiz uchun rahmat!',
        'success_praise': '✅ Minnatdorchiligingiz rahbariyatga yetkazildi! Iliq so‘zlaringiz uchun katta rahmat!',
    },
}

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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        chat_id = message.chat.id
        with buffer_lock:
            user_lang.pop(chat_id, None)
            user_pvz_key.pop(chat_id, None)
            user_action.pop(chat_id, None)
            user_category.pop(chat_id, None)
            user_media_buffer.pop(chat_id, None)
            active_dialogue.pop(chat_id, None)
            if chat_id in user_timers:
                user_timers[chat_id].cancel()
                user_timers.pop(chat_id, None)
            if chat_id in dialogue_timers:
                dialogue_timers[chat_id].cancel()
                dialogue_timers.pop(chat_id, None)

        current_pvz_key = 'pvz1'
        args = message.text.split()
        if len(args) > 1:
            param = args[1].
