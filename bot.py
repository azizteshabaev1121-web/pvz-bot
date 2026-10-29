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
user_action = {}
user_category = {}
admin_message_mapping = {}

# Ваши точки ПВЗ с обновленными адресами
PVZ_NAMES = {
    'pvz1': '📍 ПВЗ №1 ДУКЕНТ-КАСКАД (14-квартал, дом-6)',
    'pvz2': '📍 ПВЗ №2 УРИКЗОР_МАРКЕТ (ул. Ахунбабаева, дом-14/1)',
    'pvz3': '📍 ПВЗ №3 УНИВЕРСИТЕТ (ул. Узбекистон Мустакиллиги, дом-80)',
    'pvz4': '📍 ПВЗ №4 30-ЛЕТ_ЗАМИН-1 (ул. Бунёдкор, дом-210)',
}

TEXTS = {
    'ru': {
        'choose_action': 'Пожалуйста, выберите цель вашего обращения:',
        'btn_complaint': '⚠️ Пожаловаться на персонал',
        'btn_praise': '⭐️ Поблагодарить сотрудника',
        'choose_category': 'Выберите категорию проблемы:',
        'cat_1': '🗣 Грубость / Хамство',
        'cat_2': '⏳ Очередь / Медленное обслуживание',
        'cat_3': '📦 Ошибка при выдаче заказа',
        'cat_4': '📝 Другая проблема',
        'welcome_complaint': (
            'Категория: {cat}\n'
            'Точка: {pvz}\n\n'
            'Опишите подробности вашей жалобы.\n'
            '📌 Обязательно укажите дату и точное время инцидента, чтобы руководство могло проверить камеры видеонаблюдения.\n\n'
            '(Вы можете отправить текст, фото или видео).'
        ),
        'welcome_praise': (
            'Вы выбрали: Поблагодарить сотрудника (точка: {pvz}).\n\n'
            'Напишите ваши слова благодарности или отзыв о работе сотрудника.\n'
            '⭐️ Нам очень приятно слышать хорошие отзывы!\n\n'
            '(Вы можете отправить текст, фото или видео).'
        ),
        'success_complaint': '✅ Ваша жалоба и данные успешно отправлены руководству. Спасибо за помощь в улучшении сервиса!',
        'success_praise': '✅ Ваша благодарность успешно отправлена руководству! Большое спасибо за теплые слова!',
    },
    'uz': {
        'choose_action': 'Murojaatingiz turini tanlang:',
        'btn_complaint': '⚠️ Xodimdan shikoyat qilish',
        'btn_praise': '⭐️ Xodimga minnatdorchilik bildirish',
        'choose_category': 'Muammo turini tanlang:',
        'cat_1': "🗣 Qo'pol muomala / Baqirish",
        'cat_2': '⏳ Sekin xizmat / Navbat',
        'cat_3': '📦 Buyurtmadagi xatolik',
        'cat_4': '📝 Boshqa muammo',
        'welcome_complaint': (
            'Kategoriya: {cat}\n'
            'Punkt: {pvz}\n\n'
            'Shikoyatingiz tafsilotlarini yozib qoldiring.\n'
            '📌 Videokuzatuv kameralarini tekshirish uchun sana va aniq vaqtni ko‘rsatishingiz shart.\n\n'
            '(Matn, rasm yoki video yuborishingiz mumkin).'
        ),
        'welcome_praise': (
            'Siz tanladingiz: Xodimga minnatdorchilik bildirish (punkt: {pvz}).\n\n'
            'Xodimimizga minnatdorchilik so\'zlaringizni yozib qoldiring.\n'
            '⭐️ Ishimiz haqida ijobiy fikrlarni eshitishdan mamnunmiz!\n\n'
            '(Matn, rasm yoki video yuborishingiz mumkin).'
        ),
        'success_complaint': '✅ Shikoyatingiz rahbariyatga muvaffaqiyatli yuborildi. Xizmat sifatini yaxshilashga yordam berganingiz uchun rahmat!',
        'success_praise': '✅ Minnatdorchiligingiz rahbariyatga yuborildi! Iliq so\'zlaringiz uchun katta rahmat!',
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


@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        chat_id = message.chat.id
        user_lang.pop(chat_id, None)
        user_pvz.pop(chat_id, None)
        user_action.pop(chat_id, None)
        user_category.pop(chat_id, None)

        # По умолчанию ставим точку 1 для тестов без QR
        user_pvz[chat_id] = PVZ_NAMES['pvz1']

        args = message.text.split()
        if len(args) > 1:
            param = args[1].lower()
            if '2' in param or 'urikzor' in param or 'pvz2' in param:
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
            elif '1' in param or 'dukent' in param or 'pvz1' in param:
                user_pvz[chat_id] = PVZ_NAMES['pvz1']

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
    btn1 = types.InlineKeyboardButton(
        TEXTS[lang]['btn_complaint'], callback_data='action_complaint'
    )
    btn2 = types.InlineKeyboardButton(
        TEXTS[lang]['btn_praise'], callback_data='action_praise'
    )
    markup.add(btn1, btn2)
    bot.send_message(
        chat_id, TEXTS[lang]['choose_action'], reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith('action_'))
def set_action(call):
    try:
        chat_id = call.message.chat.id
        action = call.data.split('_')[1]
        user_action[chat_id] = action

        lang = user_lang.get(chat_id, 'ru')
        pvz = user_pvz.get(chat_id, 'ПВЗ')

        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            pass

        if action == 'complaint':
            markup = types.InlineKeyboardMarkup(row_width=1)
            for i in range(1, 5):
                cat_key = f'cat_{i}'
                markup.add(
                    types.InlineKeyboardButton(
                        TEXTS[lang][cat_key], callback_data=f'category_{i}'
                    )
                )
            bot.send_message(
                chat_id, TEXTS[lang]['choose_category'], reply_markup=markup
            )
        else:
            user_category[chat_id] = 'Благодарность'
            text = TEXTS[lang]['welcome_praise'].format(pvz=pvz)
            bot.send_message(
                chat_id, text, reply_markup=types.ReplyKeyboardRemove()
            )
    except Exception as e:
        print(f'Error in set_action: {e}')


@bot.callback_query_handler(func=lambda call: call.data.startswith('category_'))
def set_category(call):
    try:
        chat_id = call.message.chat.id
        cat_index = call.data.split('_')[1]
        lang = user_lang.get(chat_id, 'ru')
        pvz = user_pvz.get(chat_id, 'ПВЗ')

        cat_text = TEXTS[lang][f'cat_{cat_index}']
        user_category[chat_id] = cat_text

        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception:
            pass

        text = TEXTS[lang]['welcome_complaint'].format(
            cat=cat_text, pvz=pvz
        )
        bot.send_message(chat_id, text, reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        print(f'Error in set_category: {e}')


@bot.message_handler(
    func=lambda message: str(message.chat.id) == ADMIN_CHAT_ID
    and message.reply_to_message
)
def admin_reply(message):
    try:
        replied_id = message.reply_to_message.message_id
        client_id = admin_message_mapping.get(replied_id)

        if client_id:
            bot.send_message(
                client_id, f'💬 Ответ от руководства:\n\n{message.text}'
            )
            bot.reply_to(message, '✅ Ответ успешно отправлен клиенту!')
        else:
            bot.reply_to(
                message,
                '❌ Не удалось найти клиента. Убедитесь, что отвечаете на сообщение новой жалобы.',
            )
    except Exception as e:
        bot.reply_to(message, f'❌ Ошибка при отправке: {e}')


@bot.message_handler(
    content_types=['text', 'photo', 'video', 'document', 'audio']
)
def handle_complaint(message):
    try:
        chat_id = message.chat.id

        if (
            chat_id not in user_lang
            or chat_id not in user_pvz
            or chat_id not in user_action
            or chat_id not in user_category
        ):
            bot.send_message(
                chat_id,
                'Пожалуйста, нажмите /start для начала работы с ботом.',
            )
            return

        lang = user_lang.get(chat_id, 'ru')
        pvz = user_pvz.get(chat_id, 'ПВЗ (Точка)')
        action = user_action.get(chat_id, 'complaint')
        category = user_category.get(chat_id, 'Не указана')

        if action == 'complaint':
            bot.reply_to(message, TEXTS[lang]['success_complaint'])
            title = f'📩 Новая жалоба ({category})!'
        else:
            bot.reply_to(message, TEXTS[lang]['success_praise'])
            title = '⭐️ Новая благодарность сотруднику!'

        admin_text = (
            f'{title}\n'
            f'📍 ПВЗ: {pvz}\n'
            f'👤 От: @{message.from_user.username or message.from_user.first_name} (ID: {chat_id})'
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
    try:
        bot.remove_webhook()  # Сбрасываем зависшие вебхуки
    except Exception:
        pass
    bot.infinity_polling(skip_pending=True)
