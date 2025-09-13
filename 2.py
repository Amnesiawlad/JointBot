import telebot
from telebot import types
import datetime
import random
import string
import threading
import time
import json
import os

bot = telebot.TeleBot("8229695321:AAGRKvTLiSYeyL80QcQrVBl56h2H5anTxGk")

# Данные администратора
ADMIN_USERNAMES = ["@sevecid", "@officialamnesia"]
ADMIN_IDS = []  # Здесь будут ID админов (заполнятся через /setupap)

# Цены на подписки в долларах
PRICES = {
    "1_day": 1.0,   # 1$
    "7_days": 3.5,
    "1_month": 7.5,
    "forever": 12
}

# Типы жалоб для сноса
COMPLAINT_TYPES = {
    "personal_info": "Личная информация",
    "pornography": "Порнография",
    "illegal_goods": "Незаконные товары",
    "violence": "Насилие"
}

# Временная "база данных" (в реальном проекте используйте настоящую БД)
users = {}
payments = {}
complaint_requests = {}
admin_panel_data = {"payment_screenshots": {}}

# Путь для сохранения скриншотов оплаты
SCREENSHOTS_DIR = "payment_screenshots"
if not os.path.exists(SCREENSHOTS_DIR):
    os.makedirs(SCREENSHOTS_DIR)

class User:
    def __init__(self, user_id):
        self.id = user_id
        self.balance = 0
        self.subscription = None
        self.used_trial = False
        self.referral_code = self.generate_referral_code()
        self.referred_by = None
        self.referrals = 0
        self.earned_from_refs = 0
        self.pending_subscription_check = False
        self.username = None

    def generate_referral_code(self):
        return f"REF{self.id}"

    def has_active_subscription(self):
        return self.subscription and self.subscription > datetime.datetime.now()

    def get_referral_link(self, bot_username):
        return f"https://t.me/{bot_username}?start={self.referral_code}"

# Команда для настройки админ-панели
@bot.message_handler(commands=['setupap'])
def setup_admin_panel(message):
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь администратором по username
    user_profile = bot.get_chat(user_id)
    username = user_profile.username
    
    if username and f"@{username}" in ADMIN_USERNAMES:
        # Выдаем подписку до 2088 года
        if user_id not in users:
            users[user_id] = User(user_id)
        
        users[user_id].subscription = datetime.datetime(2088, 12, 31)
        users[user_id].balance = 9999  # Большой баланс
        
        # Добавляем в список админов
        if user_id not in ADMIN_IDS:
            ADMIN_IDS.append(user_id)
        
        # Создаем админ-панель
        markup = types.InlineKeyboardMarkup()
        view_payments_btn = types.InlineKeyboardButton("📋 Просмотреть чеки", callback_data="admin_view_payments")
        grant_sub_btn = types.InlineKeyboardButton("🎁 Выдать подписку", callback_data="admin_grant_subscription")
        stats_btn = types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")
        markup.add(view_payments_btn)
        markup.add(grant_sub_btn)
        markup.add(stats_btn)
        
        bot.send_message(
            message.chat.id,
            "✅ <b>Админ-панель активирована!</b>\n\n"
            "Вам выдана подписка до 31.12.2088\n"
            "Доступ к админ-панели предоставлен",
            parse_mode='HTML',
            reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде")

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    args = message.text.split()
    
    # Красивое приветствие
    welcome_text = f"""
🌟 <b>Добро пожаловать, {user_name}!</b> 🌟

🚀 <b>JointBot</b> - самый мощный инструмент для модерации Telegram

⚡ <b>Возможности:</b>
• Мгновенный снос аккаунтов за нарушения
• Профессиональная система жалоб
• Автоматическая отправка репортов
• Поддержка всех типов нарушений

💎 <b>Начните с бесплатного пробного сноса</b> - просто подпишитесь на наши каналы!
    """
    
    # Отправляем приветственное сообщение
    bot.send_message(message.chat.id, welcome_text, parse_mode='HTML')
    
    # Обработка реферальной ссылки
    if len(args) > 1:
        ref_code = args[1]
        # Найти пользователя с этим реферальным кодом
        for uid, user in users.items():
            if user.referral_code == ref_code and uid != user_id:
                if user_id not in users:
                    users[user_id] = User(user_id)
                users[user_id].referred_by = uid
                users[uid].referrals += 1
                users[uid].balance += 1  # Награда за реферала
                users[uid].earned_from_refs += 1
                bot.send_message(uid, f"🎉 По вашей ссылке зарегистрировался новый пользователь! Ваш баланс пополнен на 1$")
                break
    
    if user_id not in users:
        users[user_id] = User(user_id)
    
    # Сохраняем username пользователя
    users[user_id].username = message.from_user.username
    
    # Проверка подписки на каналы
    check_subscription(message)

def check_subscription(message):
    user_id = message.from_user.id
    user = users[user_id]
    
    # Показываем красивый интерфейс проверки
    markup = types.InlineKeyboardMarkup()
    channel1_btn = types.InlineKeyboardButton("📢 Канал 1", url="https://t.me/+jm_KLvITBvQ2ZjEy")
    channel2_btn = types.InlineKeyboardButton("📢 Канал 2", url="https://t.me/+M96KUMSwXMViMjFk")
    check_btn = types.InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")
    markup.add(channel1_btn, channel2_btn)
    markup.add(check_btn)
    
    # Отправляем стильное сообщение
    bot.send_message(message.chat.id, 
                    "🔥 <b>ДОСТУП К SNOSER</b>\n\n"
                    "Для получения доступа к сносеру необходимо подписаться на наши каналы:\n\n"
                    "📢 <b>Канал 1</b> - основной канал проекта\n"
                    "📢 <b>Канал 2</b> - новости и обновления\n\n"
                    "После подписки нажмите кнопку <b>\"Я подписался\"</b> для проверки\n\n"
                    "💎 <b>После проверки вы получите 1 БЕСПЛАТНЫЙ снос на 40 аккаунтов!</b>",
                    parse_mode='HTML', 
                    reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'check_subscription')
def handle_check_subscription(call):
    user_id = call.from_user.id
    user = users[user_id]
    
    if user.pending_subscription_check:
        bot.answer_callback_query(call.id, "⏳ Ваша заявка уже проверяется, пожалуйста, подождите")
        return
    
    user.pending_subscription_check = True
    
    # Удаляем предыдущее сообщение
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    # Отправляем сообщение о проверке
    msg = bot.send_message(call.message.chat.id, "⏳ <b>Проверяем подписку...</b>", parse_mode='HTML')
    
    # Запускаем проверку в отдельном потоке
    thread = threading.Thread(target=check_subscription_thread, args=(user_id, msg.message_id, call.message.chat.id))
    thread.start()

def check_subscription_thread(user_id, message_id, chat_id):
    time.sleep(3)  # Имитация проверки
    
    if user_id in users:
        users[user_id].pending_subscription_check = False
        
        # Здесь должна быть реальная проверка подписки
        # В данном случае просто даем доступ
        users[user_id].used_trial = True
        users[user_id].balance += 1
        
        try:
            bot.edit_message_text(
                "✅ <b>Подписка подтверждена!</b>\n\n"
                "🎉 Вам выдан <b>1 БЕСПЛАТНЫЙ снос</b> на 40 аккаунтов!\n\n"
                "⚠️ <b>Внимание:</b> В бесплатном режиме шанс успешного сноса ниже, чем в платном.\n"
                "В платном режиме мы отправляем до 500 жалоб моментально!",
                chat_id,
                message_id,
                parse_mode='HTML'
            )
            time.sleep(2)
            show_main_menu(chat_id)
        except:
            pass  # Игнорируем ошибки отправки

def show_main_menu(chat_id, text=None):
    if text is None:
        text = "🌐 <b>Главное меню</b>"
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("👤 Профиль")
    btn2 = types.KeyboardButton("🤝 Подписка")
    btn3 = types.KeyboardButton("🌀 Сносер")
    btn4 = types.KeyboardButton("💳 Пополнить")
    btn5 = types.KeyboardButton("👥 Рефералы")
    btn6 = types.KeyboardButton("🛠️ Поддержка")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
    bot.send_message(chat_id, text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def profile(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = User(user_id)
    
    user = users[user_id]
    sub_status = "✅ Активна" if user.has_active_subscription() else "❌ Неактивна"
    
    # Получаем username бота для реферальной ссылки
    bot_info = bot.get_me()
    bot_username = bot_info.username
    
    # Создаем красивый профиль
    text = f"""
<b>👤 ВАШ ПРОФИЛЬ</b>

<b>🆔 ID:</b> <code>{user_id}</code>
<b>👤 Username:</b> @{user.username if user.username else 'не установлен'}
<b>💰 Баланс:</b> <b>{user.balance}$</b>
<b>🔐 Подписка:</b> {sub_status}
<b>👥 Рефералов:</b> {user.referrals}
<b>🎯 Заработано с рефералов:</b> {user.earned_from_refs}$
<b>🔗 Реферальная ссылка:</b> 
<code>{user.get_referral_link(bot_username)}</code>
"""
    
    if user.has_active_subscription():
        remaining = user.subscription - datetime.datetime.now()
        text += f"\n<b>⏰ Осталось:</b> {remaining.days} дн, {remaining.seconds//3600} ч"
    
    markup = types.InlineKeyboardMarkup()
    withdraw_btn = types.InlineKeyboardButton("💳 Вывести средства", callback_data="withdraw")
    markup.add(withdraw_btn)
    
    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🌀 Сносер")
def snoser(message):
    user_id = message.from_user.id
    if user_id not in users:
        users[user_id] = User(user_id)
    
    user = users[user_id]
    
    # Проверяем, есть ли активная подписка или бесплатный доступ
    if not user.has_active_subscription() and user.balance < 1:
        bot.send_message(message.chat.id, 
                        "❌ <b>Доступ закрыт</b>\n\nДля использования сносера требуется активная подписка или баланс.\n\n"
                        "💎 <b>Подпишитесь на наши каналы для получения БЕСПЛАТНОГО доступа к 1 сносу</b>\n"
                        "или приобретите подписку в разделе <b>\"🤝 Подписка\"</b>",
                        parse_mode='HTML')
        return
    
    # Показываем меню выбора типа жалобы
    markup = types.InlineKeyboardMarkup()
    for key, value in COMPLAINT_TYPES.items():
        markup.add(types.InlineKeyboardButton(value, callback_data=f"complaint_{key}"))
    
    bot.send_message(
        message.chat.id,
        "🔍 <b>Выберите тип нарушения:</b>\n\n"
        "• <b>Личная информация</b> - раскрытие персональных данных\n"
        "• <b>Порнография</b> - распространение материалов для взрослых\n"
        "• <b>Незаконные товары</b> - продажа запрещенных веществ/товаров\n"
        "• <b>Насилие</b> - призывы к насилию, угрозы\n\n"
        "⚠️ <b>Внимание:</b> Необоснованные жалобы могут привести к блокировке вашего аккаунта",
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('complaint_'))
def handle_complaint_type(call):
    user_id = call.from_user.id
    complaint_type = call.data.split('_')[1]
    
    # Сохраняем тип жалобы
    if user_id not in complaint_requests:
        complaint_requests[user_id] = {}
    
    complaint_requests[user_id]['type'] = complaint_type
    
    # Удаляем предыдущее сообщение
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    
    # Просим username или ссылку
    bot.send_message(
        call.message.chat.id,
        "📝 <b>Введите username или ссылку на аккаунт/канал:</b>\n\n"
        "Примеры:\n"
        "• <code>@username</code>\n"
        "• <code>https://t.me/username</code>\n"
        "• <code>https://t.me/c/123456789/123</code>",
        parse_mode='HTML'
    )
    
    # Регистрируем следующий шаг
    bot.register_next_step_handler(call.message, process_username_input)

def process_username_input(message):
    user_id = message.from_user.id
    
    if user_id not in complaint_requests:
        complaint_requests[user_id] = {}
    
    complaint_requests[user_id]['target'] = message.text
    
    # Просим ID аккаунта или канала
    bot.send_message(
        message.chat.id,
        "🔢 <b>Введите ID аккаунта или канала:</b>\n\n"
        "⚠️ <b>Важно:</b> ID должен быть числовым идентификатором\n"
        "Для получения ID используйте ботов типа @username_to_id_bot",
        parse_mode='HTML'
    )
    
    # Регистрируем следующий шаг
    bot.register_next_step_handler(message, process_id_input)

def process_id_input(message):
    user_id = message.from_user.id
    
    if user_id not in complaint_requests:
        complaint_requests[user_id] = {}
    
    complaint_requests[user_id]['target_id'] = message.text
    
    # Просим ссылки на нарушения
    bot.send_message(
        message.chat.id,
        "📎 <b>Пришлите ссылки на нарушения:</b>\n\n"
        "• Можно приложить несколько ссылок\n"
        "• Каждая ссылка с новой строки\n"
        "• Убедитесь, что ссылки рабочие\n\n"
        "Пример:\n"
        "<code>https://t.me/c/123456789/1</code>\n"
        "<code>https://t.me/c/123456789/2</code>",
        parse_mode='HTML'
    )
    
    # Регистрируем следующий шаг
    bot.register_next_step_handler(message, process_links_input)

def process_links_input(message):
    user_id = message.from_user.id
    
    if user_id not in complaint_requests:
        complaint_requests[user_id] = {}
    
    complaint_requests[user_id]['violation_links'] = message.text.split('\n')
    
    # Проверяем, есть ли у пользователя активная подписка
    user = users[user_id]
    is_paid = user.has_active_subscription()
    
    # Определяем количество жалоб
    complaint_count = 500 if is_paid else 40
    
    # Формируем подтверждение
    complaint_type = COMPLAINT_TYPES.get(complaint_requests[user_id]['type'], "Неизвестно")
    
    text = f"""
✅ <b>Данные получены!</b>

<b>Тип нарушения:</b> {complaint_type}
<b>Цель:</b> {complaint_requests[user_id]['target']}
<b>ID цели:</b> {complaint_requests[user_id]['target_id']}
<b>Количество ссылок:</b> {len(complaint_requests[user_id]['violation_links'])}
<b>Режим:</b> {'💎 ПЛАКТНЫЙ (500 жалоб)' if is_paid else '🎁 БЕСПЛАТНЫЙ (40 жалоб)'}

<b>Статус:</b> ⏳ Отправка...
"""
    
    # Отправляем подтверждение
    msg = bot.send_message(message.chat.id, text, parse_mode='HTML')
    
    # Имитируем процесс отправки
    time.sleep(2)
    
    # Обновляем статус
    success_count = complaint_count if is_paid else random.randint(30, 40)
    
    text += f"\n<b>Статус:</b> ✅ Успешно отправлено!\n<b>Жалоб отправлено:</b> {success_count}/{complaint_count}"
    
    bot.edit_message_text(
        text,
        message.chat.id,
        msg.message_id,
        parse_mode='HTML'
    )
    
    # Снимаем средства, если это не подписка
    if not is_paid:
        user.balance -= 1
    
    # Показываем главное меню
    show_main_menu(message.chat.id)

# Обработка админ-панели
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_panel(call):
    user_id = call.from_user.id
    
    if user_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ У вас нет доступа к админ-панели")
        return
    
    if call.data == "admin_view_payments":
        # Показываем список скриншотов оплаты
        if not admin_panel_data["payment_screenshots"]:
            bot.answer_callback_query(call.id, "📭 Нет ожидающих скриншотов")
            return
        
        text = "📋 <b>Ожидающие скриншоты оплаты:</b>\n\n"
        
        markup = types.InlineKeyboardMarkup()
        
        for payment_id, data in admin_panel_data["payment_screenshots"].items():
            user_info = f"Пользователь: {data['user_id']}"
            if data.get('username'):
                user_info += f" (@{data['username']})"
            
            text += f"• <b>ID:</b> {payment_id}\n{user_info}\n<b>Сумма:</b> {data['amount']}$\n\n"
            
            markup.add(types.InlineKeyboardButton(
                f"Просмотр {payment_id}", 
                callback_data=f"admin_view_payment_{payment_id}"
            ))
        
        markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="admin_back"))
        
        try:
            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='HTML',
                reply_markup=markup
            )
        except:
            pass
    
    elif call.data == "admin_grant_subscription":
        # Запрос на выдачу подписки
        bot.send_message(
            call.message.chat.id,
            "👤 <b>Введите ID пользователя для выдачи подписки:</b>\n\n"
            "Формат: <code>123456789</code>",
            parse_mode='HTML'
        )
        
        # Регистрируем следующий шаг
        bot.register_next_step_handler(call.message, process_grant_subscription)
    
    elif call.data.startswith("admin_view_payment_"):
        # Просмотр конкретного скриншота
        payment_id = call.data.split('_')[-1]
        
        if payment_id in admin_panel_data["payment_screenshots"]:
            data = admin_panel_data["payment_screenshots"][payment_id]
            
            # Отправляем скриншот
            try:
                with open(data['file_path'], 'rb') as photo:
                    bot.send_photo(
                        call.message.chat.id,
                        photo,
                        caption=f"📸 <b>Скриншот оплаты</b>\n\n"
                               f"<b>ID платежа:</b> {payment_id}\n"
                               f"<b>Пользователь:</b> {data['user_id']}\n"
                               f"<b>Username:</b> @{data.get('username', 'неизвестно')}\n"
                               f"<b>Сумма:</b> {data['amount']}$\n"
                               f"<b>Тип:</b> {data.get('type', 'пополнение')}",
                        parse_mode='HTML'
                    )
            except:
                bot.send_message(
                    call.message.chat.id,
                    "❌ Не удалось загрузить скриншот",
                    parse_mode='HTML'
                )
        else:
            bot.answer_callback_query(call.id, "❌ Скриншот не найден")

def process_grant_subscription(message):
    user_id = message.from_user.id
    
    try:
        target_id = int(message.text)
        
        # Запрашиваем тип подписки
        markup = types.InlineKeyboardMarkup()
        day_btn = types.InlineKeyboardButton("1 день", callback_data=f"admin_grant_1_day_{target_id}")
        week_btn = types.InlineKeyboardButton("7 дней", callback_data=f"admin_grant_7_days_{target_id}")
        month_btn = types.InlineKeyboardButton("1 месяц", callback_data=f"admin_grant_1_month_{target_id}")
        forever_btn = types.InlineKeyboardButton("Навсегда", callback_data=f"admin_grant_forever_{target_id}")
        markup.add(day_btn, week_btn)
        markup.add(month_btn, forever_btn)
        
        bot.send_message(
            message.chat.id,
            f"🕐 <b>Выберите срок подписки для пользователя {target_id}:</b>",
            parse_mode='HTML',
            reply_markup=markup
        )
    except:
        bot.send_message(message.chat.id, "❌ Неверный формат ID")

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_grant_'))
def handle_grant_subscription(call):
    user_id = call.from_user.id
    
    if user_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ У вас нет доступа")
        return
    
    parts = call.data.split('_')
    duration = parts[2]  # day, days, month, forever
    target_id = int(parts[3])
    
    # Создаем пользователя, если его нет
    if target_id not in users:
        users[target_id] = User(target_id)
    
    # Выдаем подписку
    now = datetime.datetime.now()
    
    if duration == "day":
        users[target_id].subscription = now + datetime.timedelta(days=1)
    elif duration == "days":
        users[target_id].subscription = now + datetime.timedelta(days=7)
    elif duration == "month":
        users[target_id].subscription = now + datetime.timedelta(days=30)
    elif duration == "forever":
        users[target_id].subscription = datetime.datetime(2088, 12, 31)
    
    # Уведомляем администратора
    duration_text = {
        "day": "1 день",
        "days": "7 дней",
        "month": "1 месяц",
        "forever": "НАВСЕГДА (до 2088)"
    }
    
    bot.send_message(
        call.message.chat.id,
        f"✅ <b>Подписка выдана!</b>\n\n"
        f"<b>Пользователь:</b> {target_id}\n"
        f"<b>Срок:</b> {duration_text[duration]}\n"
        f"<b>Истекает:</b> {users[target_id].subscription.strftime('%Y-%m-%d %H:%M')}",
        parse_mode='HTML'
    )
    
    # Уведомляем пользователя, если возможно
    try:
        bot.send_message(
            target_id,
            f"🎉 <b>Вам выдана подписка!</b>\n\n"
            f"Администратор предоставил вам доступ к JointBot\n"
            f"<b>Срок:</b> {duration_text[duration]}\n"
            f"<b>Истекает:</b> {users[target_id].subscription.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Теперь вы можете использовать все возможности бота!",
            parse_mode='HTML'
        )
    except:
        pass  # Не удалось отправить уведомление

# Обработка скриншотов оплаты
@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    user_id = message.from_user.id
    
    # Проверяем, ожидаем ли мы скриншот от этого пользователя
    for payment_id, payment in payments.items():
        if payment["user_id"] == user_id and payment.get("waiting_for_screenshot", False):
            # Сохраняем скриншот
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            file_path = os.path.join(SCREENSHOTS_DIR, f"{payment_id}.jpg")
            with open(file_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            # Добавляем в админ-панель
            admin_panel_data["payment_screenshots"][payment_id] = {
                "user_id": user_id,
                "username": message.from_user.username,
                "amount": payment["amount"],
                "type": payment.get("type", "пополнение"),
                "file_path": file_path
            }
            
            # Обновляем статус платежа
            payment["status"] = "processing"
            payment["waiting_for_screenshot"] = False
            
            # Уведомляем пользователя
            bot.send_message(
                message.chat.id,
                "✅ <b>Скриншот отправлен на проверку!</b>\n\n"
                "Ожидайте подтверждения оплаты. Обычно это занимает не более 5 минут.\n"
                "Если у вас возникли проблемы, обратитесь в поддержку: @sevecid или @officialamnesia",
                parse_mode='HTML'
            )
            
            # Уведомляем администраторов
            for admin_id in ADMIN_IDS:
                try:
                    bot.send_message(
                        admin_id,
                        f"📸 <b>Новый скриншот оплаты!</b>\n\n"
                        f"<b>Пользователь:</b> {user_id} (@{message.from_user.username})\n"
                        f"<b>Сумма:</b> {payment['amount']}$\n"
                        f"<b>ID платежа:</b> {payment_id}",
                        parse_mode='HTML'
                    )
                except:
                    pass
            
            break

# Запуск бота
if __name__ == "__main__":
    print("🔥 Бот JointBot запущен...")
    bot.polling(none_stop=True)