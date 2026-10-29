import os
import time
from threading import Thread
from flask import Flask
import telebot
from telebot import types
import requests

TOKEN = '9006379873:AAFAqMpfyhsk3pPXT53OFs7tHwOue9FsH4o'
ADMIN_CHAT_ID = '8208422375'
GOOGLE_SHEET_WEB_APP_URL = 'https://script.google.com/macros/s/AKfycbwh1QwChd9BMCX1xVcbnY81-DwEx5oYFYYQArvhCBS_mcqeXpjjIH31GQZpHeYNaTn-Zw/exec'

bot = telebot.TeleBot(TOKEN)

user_lang = {}
user_pvz_key = {}
user_action = {}
user_category = {}
admin_message_mapping = {}

# Названия и адреса для русского языка (ПВЗ)
PVZ_NAMES_RU = {
    'pvz1': '📍 ПВЗ №1 ДУКЕНТ-КАСКАД (14-квартал, дом-6)',
    'pvz2': '📍 ПВЗ №2 УРИКЗОР_МАРКЕТ (ул. Ахунбабаева, дом-14/1)',
    'pvz3': '📍 ПВЗ №3 УНИВЕРСИТЕТ (ул. Узбекистон Мустакиллиги, дом-80)',
    'pvz4': '📍 ПВЗ №4 30-ЛЕТ_ЗАМИН-1 (ул. Бунёдкор, дом-210)',
}

# Названия и адреса для узбекского языка (BTP)
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
            '📌 Если это связано с инцидентом, укажите дату и примерное время, чтобы руководство могло проверить камеры.\n\n'
            '(Вы можете отправить текст, фото или видео).'
        ),
        'welcome_praise': (
            'Вы выбрали: Поблагодарить сотрудника (точка: {pvz}).\n\n'
            'Напишите ваши слова благодарности или отзыв о работе сотрудника.\n'
            '⭐️ Нам очень приятно слышать хорошие отзывы!\n\n'
            '(Вы можете отправить текст, фото или видео).'
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
            '📌 Videokuzatuv kameralarini tekshirish uchun sana va taxminiy vaqtni ko‘rsatishingiz mumkin.\n\n'
            '(Matn, rasm yoki video yuborishingiz mumkin).'
        ),
        'welcome_praise': (
            'Siz tanladingiz: Xodimga minnatdorchilik bildirish (punkt: {pvz}).\n\n'
            'Xodimimizga minnatdorchilik so\'zlaringizni yozib qoldiring.\n'
            '⭐️ Ishimiz haqida ijobiy fikrlarni eshitishdan mamnunmiz!\n\n'
            '(Matn, rasm yoki video yuborishingiz mumkin).'
        ),
        'success_complaint': '✅ Murojaatingiz BTP rahbariyatiga muvaffaqiyatli yuborildi. Xizmat sifatini yaxshilashga yordam berganingiz uchun rahmat!',
        'success_praise': '✅ Minnatdorchiligingiz rahbariyatga yetkazildi! Iliq so\'zlaringiz uchun katta rahmat!',
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
        user_lang.pop(chat_id, None)
        user_pvz_key.pop(chat_id, None)
        user_action.pop(chat_id, None)
        user_category.pop(chat_id, None)

        current_pvz_key = 'pvz1'
        args = message.text.split()
        if len(args) > 1:
            param = args[1].lower()
            if '2' in param or 'urikzor' in param or 'pvz2' in param:
                current_pvz_key = 'pvz2'
            elif '3' in param or 'universitet' in param or 'pvz3' in param:
                current_pvz_key = 'pvz3'
            elif '4' in param or 'zamin' in param or 'bunyodkor' in param or 'angren' in param or 'pvz4' in param:
                current_pvz_key = 'pvz4'
            elif '1' in param or 'dukent' in param or 'pvz1' in param:
                current_pvz_key = 'pvz1'

        user_pvz_key[chat_id] = current_pvz_key

        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_ru = types.InlineKeyboardButton('🇷🇺 Русский', callback_data='lang_ru')
        btn_uz = types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data='lang_uz')
        markup.add(btn_ru, btn_uz)

        bot.send_message(
            chat_id,
            'Здравствуйте! Пожалуйста, выберите язык / Tilni tanlang:',
            reply_markup=markup,
        )
    except Exception as e:
        print(f'Error in send_welcome: {e}')

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    try:
        chat_id = call.message.chat.id
        lang = call.data.split('_')[1]
        user_lang[chat_id] = lang

        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            pass

        show_action_menu(chat_id, lang)
    except Exception as e:
        print(f'Error in set_language: {e}')

def show_action_menu(chat_id, lang):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton(TEXTS[lang]['btn_complaint'], callback_data='action_complaint')
    btn2 = types.InlineKeyboardButton(TEXTS[lang]['btn_praise'], callback_data='action_praise')
    markup.add(btn1, btn2)
    bot.send_message(chat_id, TEXTS[lang]['choose_action'], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('action_'))
def set_action(call):
    try:
        chat_id = call.message.chat.id
        action = call.data.split('_')[1]
        user_action[chat_id] = action

        lang = user_lang.get(chat_id, 'ru')
        p_key = user_pvz_key.get(chat_id, 'pvz1')
        pvz = PVZ_NAMES_RU[p_key] if lang == 'ru' else PVZ_NAMES_UZ[p_key]

        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            pass

        if action == 'complaint':
            markup = types.InlineKeyboardMarkup(row_width=1)
            for i in range(1, 6):
                cat_key = f'cat_{i}'
                markup.add(types.InlineKeyboardButton(TEXTS[lang][cat_key], callback_data=f'category_{i}'))
            bot.send_message(chat_id, TEXTS[lang]['choose_category'], reply_markup=markup)
        else:
            user_category[chat_id] = 'Благодарность' if lang == 'ru' else 'Minnatdorchilik'
            text = TEXTS[lang]['welcome_praise'].format(pvz=pvz)
            bot.send_message(chat_id, text, reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        print(f'Error in set_action: {e}')

@bot.callback_query_handler(func=lambda call: call.data.startswith('category_'))
def set_category(call):
    try:
        chat_id = call.message.chat.id
        cat_index = call.data.split('_')[1]
        lang = user_lang.get(chat_id, 'ru')
        p_key = user_pvz_key.get(chat_id, 'pvz1')
        pvz = PVZ_NAMES_RU[p_key] if lang == 'ru' else PVZ_NAMES_UZ[p_key]

        cat_text = TEXTS[lang][f'cat_{cat_index}']
        user_category[chat_id] = cat_text

        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            pass

        text = TEXTS[lang]['welcome_complaint'].format(cat=cat_text, pvz=pvz)
        bot.send_message(chat_id, text, reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        print(f'Error in set_category: {e}')

@bot.message_handler(func=lambda message: str(message.chat.id) == ADMIN_CHAT_ID and message.reply_to_message)
def admin_reply(message):
    try:
        replied_id = message.reply_to_message.message_id
        client_id = admin_message_mapping.get(replied_id)

        if client_id:
            bot.send_message(client_id, f'💬 Ответ от руководства:\n\n{message.text}')
            bot.reply_to(message, '✅ Ответ успешно отправлен клиенту!')
        else:
            bot.reply_to(message, '❌ Не удалось найти клиента. Убедитесь, что отвечаете на сообщение нового обращения.')
    except Exception as e:
        bot.reply_to(message, f'❌ Ошибка при отправке: {e}')

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio'])
def handle_complaint(message):
    try:
        chat_id = message.chat.id

        if chat_id not in user_lang or chat_id not in user_pvz_key or chat_id not in user_action or chat_id not in user_category:
            bot.send_message(chat_id, 'Пожалуйста, нажмите /start для начала работы с ботом.')
            return

        lang = user_lang.get(chat_id, 'ru')
        p_key = user_pvz_key.get(chat_id, 'pvz1')
        pvz = PVZ_NAMES_RU[p_key] if lang == 'ru' else PVZ_NAMES_UZ[p_key]
        action = user_action.get(chat_id, 'complaint')
        category = user_category.get(chat_id, 'Не указана')

        if action == 'complaint':
            bot.reply_to(message, TEXTS[lang]['success_complaint'])
            title = f'📩 Обращение к руководству ПВЗ ({category})!' if lang == 'ru' else f'📩 BTP rahbariyatiga murojaat ({category})!'
            action_name = 'Обращение ПВЗ' if lang == 'ru' else 'BTP Murojaat'
        else:
            bot.reply_to(message, TEXTS[lang]['success_praise'])
            title = '⭐️ Новая благодарность сотруднику!' if lang == 'ru' else '⭐️ Xodimga yangi minnatdorchilik!'
            action_name = 'Благодарность' if lang == 'ru' else 'Minnatdorchilik'

        client_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {chat_id}"
        text_content = message.text or message.caption or '[Медиафайл]'

        try:
            payload = {
                'pvz': pvz,
                'action': action_name,
                'category': category,
                'client': client_info,
                'text': text_content
            }
            requests.post(GOOGLE_SHEET_WEB_APP_URL, json=payload, timeout=5)
        except Exception as sheet_err:
            print(f'Google Sheets error: {sheet_err}')

        label_pvz = 'ПВЗ' if lang == 'ru' else 'BTP'
        admin_text = (
            f'{title}\n'
            f'📍 {label_pvz}: {pvz}\n'
            f'👤 От: {client_info}'
        )

        msg1 = bot.send_message(ADMIN_CHAT_ID, admin_text)
        msg2 = bot.forward_message(ADMIN_CHAT_ID, chat_id, message.message_id)

        admin_message_mapping[msg1.message_id] = chat_id
        admin_message_mapping[msg2.message_id] = chat_id
    except Exception as e:
        print(f'Error in handle_complaint: {e}')

if __name__ == '__main__':
    keep_alive()
    print('Бот запущен в облаке...')
    time.sleep(5)
    try:
        bot.remove_webhook()
    except Exception:
        pass
    bot.infinity_polling(skip_pending=True, interval=2, timeout=20)
