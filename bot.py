import os
import time
import threading
from threading import Thread
from flask import Flask
import telebot
from telebot import types
import requests

TOKEN = '9006379873:AAFAqMpfyhsk3pPXT53OFs7tHwOue9FsH4o'
ADMIN_CHAT_ID = '8208422375'
GOOGLE_SHEET_WEB_APP_URL = 'https://script.google.com/macros/s/AKfycbw7noXOdNchqU3uBQqCx6nMngWrxIiroF4gqOawUZPyPRieZ-7oAlR8UaYkfrNgWYuc/exec'

bot = telebot.TeleBot(TOKEN)

user_lang = {}
user_pvz_key = {}
user_action = {}
user_category = {}
user_media_buffer = {}  
user_timers = {}        
admin_message_mapping = {}
active_dialogue = {}    

buffer_lock = threading.Lock()  

MAX_FILES_LIMIT = 10                  
MAX_FILE_SIZE_MB = 20                 
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  
MAX_MAPPING_SIZE = 500                

def add_to_mapping(msg_id, client_id):
    with buffer_lock:
        admin_message_mapping[msg_id] = client_id
        if len(admin_message_mapping) > MAX_MAPPING_SIZE:
            oldest_key = next(iter(admin_message_mapping))
            admin_message_mapping.pop(oldest_key, None)

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
            user_media_buffer[chat_id] = []
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
        user_media_buffer[chat_id] = []

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
            msg_sent = bot.send_message(client_id, f'💬 Ответ от руководства:\n\n{message.text}')
            add_to_mapping(msg_sent.message_id, client_id)
            
            # Обновляем ту же строку в таблице
            try:
                payload = {
                    'type': 'admin_reply',
                    'client': str(client_id),
                    'text': message.text
                }
                requests.post(GOOGLE_SHEET_WEB_APP_URL, json=payload, timeout=5)
            except Exception as sheet_err:
                print(f'Google Sheets error on admin reply: {sheet_err}')

            bot.reply_to(message, '✅ Ответ отправлен клиенту и записан в строку таблицы!')
        else:
            bot.reply_to(message, '❌ Не удалось найти клиента. Убедитесь, что отвечаете на сообщение нового обращения.')
    except Exception as e:
        bot.reply_to(message, f'❌ Ошибка при отправке: {e}')

def send_buffered_appeal(chat_id):
    try:
        with buffer_lock:
            if chat_id not in user_media_buffer or not user_media_buffer[chat_id]:
                return

            buffer = user_media_buffer[chat_id]
            lang = user_lang.get(chat_id, 'ru')
            p_key = user_pvz_key.get(chat_id, 'pvz1')
            pvz = PVZ_NAMES_RU[p_key] if lang == 'ru' else PVZ_NAMES_UZ[p_key]
            action = user_action.get(chat_id, 'complaint')
            category = user_category.get(chat_id, 'Не указана')

            user_media_buffer.pop(chat_id, None)
            if chat_id in user_timers:
                user_timers[chat_id].cancel()
                user_timers.pop(chat_id, None)

        if action == 'complaint':
            success_text = TEXTS[lang]['success_complaint']
            title = f'📩 Обращение к руководству ПВЗ ({category})!' if lang == 'ru' else f'📩 BTP rahbariyatiga murojaat ({category})!'
            action_name = 'Обращение ПВЗ' if lang == 'ru' else 'BTP Murojaat'
        else:
            success_text = TEXTS[lang]['success_praise']
            title = '⭐️ Новая благодарность сотруднику!' if lang == 'ru' else '⭐️ Xodimga yangi minnatdorchilik!'
            action_name = 'Благодарность' if lang == 'ru' else 'Minnatdorchilik'

        first_msg = buffer[0]
        client_info = f"@{first_msg.from_user.username}" if first_msg.from_user.username else f"ID: {chat_id}"

        all_texts = []
        has_media = False
        for msg in buffer:
            txt = msg.text or msg.caption
            if txt:
                all_texts.append(txt)
            if msg.content_type in ['photo', 'video', 'document', 'audio']:
                has_media = True

        combined_text = " \n".join(all_texts) if all_texts else ("[Медиафайлы без текста]" if has_media else "Обращение без текста")

        try:
            payload = {
                'pvz': pvz,
                'action': action_name,
                'category': category,
                'client': client_info,
                'text': combined_text
            }
            requests.post(GOOGLE_SHEET_WEB_APP_URL, json=payload, timeout=5)
        except Exception as sheet_err:
            print(f'Google Sheets error: {sheet_err}')

        label_pvz = 'ПВЗ' if lang == 'ru' else 'BTP'
        admin_text = (
            f'{title}\n'
            f'📍 {label_pvz}: {pvz}\n'
            f'👤 От: {client_info}\n'
            f'💬 Описание: {combined_text}'
        )

        msg1 = bot.send_message(ADMIN_CHAT_ID, admin_text)
        add_to_mapping(msg1.message_id, chat_id)

        for msg in buffer:
            if msg.content_type in ['photo', 'video', 'document', 'audio']:
                try:
                    msg_f = bot.forward_message(ADMIN_CHAT_ID, chat_id, msg.message_id)
                    add_to_mapping(msg_f.message_id, chat_id)
                except Exception:
                    pass

        bot.send_message(chat_id, success_text)

        with buffer_lock:
            user_lang.pop(chat_id, None)
            user_pvz_key.pop(chat_id, None)
            user_action.pop(chat_id, None)
            user_category.pop(chat_id, None)
            active_dialogue[chat_id] = True

    except Exception as e:
        print(f'Error in send_buffered_appeal: {e}')

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio'])
def handle_complaint(message):
    try:
        chat_id = message.chat.id

        with buffer_lock:
            if active_dialogue.get(chat_id):
                client_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {chat_id}"
                
                if message.content_type == 'text':
                    admin_text = f"💬 Ответ от клиента ({client_info}):\n\n{message.text}"
                    msg_forwarded = bot.send_message(ADMIN_CHAT_ID, admin_text)
                    add_to_mapping(msg_forwarded.message_id, chat_id)
                else:
                    caption = f"💬 Медиа-ответ от клиента ({client_info})" + (f": {message.caption}" if message.caption else "")
                    msg_forwarded = bot.copy_message(ADMIN_CHAT_ID, chat_id, message.message_id, caption=caption)
                    add_to_mapping(msg_forwarded.message_id, chat_id)
                
                bot.reply_to(message, "✅ Ваше сообщение отправлено руководству.")
                return

            if chat_id not in user_lang or chat_id not in user_pvz_key or chat_id not in user_action or chat_id not in user_category:
                bot.send_message(chat_id, 'Пожалуйста, нажмите /start для начала работы с ботом.')
                return

            lang = user_lang.get(chat_id, 'ru')

            file_size = 0
            if message.video:
                file_size = message.video.file_size or 0
            elif message.document:
                file_size = message.document.file_size or 0
            elif message.audio:
                file_size = message.audio.file_size or 0
            elif message.photo:
                file_size = message.photo[-1].file_size or 0

            if file_size > MAX_FILE_SIZE_BYTES:
                warning_text = (
                    f'⚠️ Этот файл слишком большой! Максимальный размер одного файла — {MAX_FILE_SIZE_MB} МБ.'
                    if lang == 'ru'
                    else f'⚠️ Bu fayl juda katta! Har bir fayl uchun maksimal hajm — {MAX_FILE_SIZE_MB} MB.'
                )
                bot.send_message(chat_id, warning_text)
                return

            if chat_id not in user_media_buffer:
                user_media_buffer[chat_id] = []

            if len(user_media_buffer[chat_id]) >= MAX_FILES_LIMIT:
                if chat_id in user_timers:
                    user_timers[chat_id].cancel()
                    user_timers.pop(chat_id, None)
                threading.Thread(target=send_buffered_appeal, args=(chat_id,)).start()
                bot.send_message(chat_id, f'⚠️ Достигнут лимит в {MAX_FILES_LIMIT} файлов. Ваше обращение отправлено автоматически.')
                return

            user_media_buffer[chat_id].append(message)

            if chat_id in user_timers:
                user_timers[chat_id].cancel()

            timer = threading.Timer(8.0, send_buffered_appeal, args=[chat_id])
            user_timers[chat_id] = timer
            timer.start()

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

    try:
        pinned_msg = bot.send_message(ADMIN_CHAT_ID, PINNED_TEMPLATES_TEXT, parse_mode="Markdown")
        bot.pin_chat_message(ADMIN_CHAT_ID, pinned_msg.message_id)
        print('Шаблоны успешно отправлены и закреплены в чате администратора!')
    except Exception as pin_err:
        print(f'Не удалось закрепить шаблоны (возможно, бот не админ в чате): {pin_err}')

    bot.infinity_polling(skip_pending=True, interval=2, timeout=20)
