import logging
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ConversationHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Данные бота (из переменных окружения или значения по умолчанию)
TOKEN = os.environ.get('BOT_TOKEN', "8246616088:AAE8s7jnjgC9TDK-q8T3UF4ZMmyn54QzRGU")

# Логируем информацию о токене (без самого токена для безопасности)
if os.environ.get('BOT_TOKEN'):
    logger.info("BOT_TOKEN загружен из переменных окружения")
else:
    logger.warning("BOT_TOKEN не найден в переменных окружения, используется значение по умолчанию")

MAIN_ADMIN_ID = 1349829403
ALL_ADMIN_IDS = [1349829403, 5320953310, 6231170714]  # Все администраторы
PROJECT_NAME = "VibeMc | Персонал"

# Состояния для ConversationHandler
MODER_NICKNAME, MODER_DONATE, MODER_FULLNAME, MODER_AGE, MODER_TIME, MODER_EXPERIENCE, MODER_ABOUT = range(7)
MEDIA_NICKNAME, MEDIA_FULLNAME, MEDIA_AGE, MEDIA_PLATFORM, MEDIA_STATS, MEDIA_ABOUT, MEDIA_LINKS = range(7)
REJECT_REASON = 100

# Хранилище заявок
applications = {}
application_counter = 1

# Функции для работы с файлом
def save_applications():
    """Сохраняет заявки в файл"""
    try:
        with open('applications.json', 'w', encoding='utf-8') as f:
            data_to_save = {
                'applications': applications,
                'application_counter': application_counter
            }
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        logger.info("Заявки сохранены в файл")
    except Exception as e:
        logger.error(f"Ошибка сохранения заявок: {e}")

def load_applications():
    """Загружает заявки из файла"""
    global applications, application_counter
    try:
        with open('applications.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            applications = data.get('applications', {})
            application_counter = data.get('application_counter', 1)
        logger.info(f"Загружено {len(applications)} заявок")
    except FileNotFoundError:
        applications = {}
        application_counter = 1
        logger.info("Файл с заявками не найден, создаем новый")
    except Exception as e:
        logger.error(f"Ошибка загрузки заявок: {e}")
        applications = {}
        application_counter = 1

def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    return user_id in ALL_ADMIN_IDS

def can_view_moder(user_id):
    """Проверяет, может ли пользователь просматривать заявки модераторов"""
    return user_id in ALL_ADMIN_IDS  # Все три админа могут просматривать

def can_manage_moder(user_id):
    """Проверяет, может ли пользователь принимать/отклонять заявки модераторов"""
    return user_id == MAIN_ADMIN_ID  # Только главный админ может управлять

def can_view_media(user_id):
    """Проверяет, может ли пользователь просматривать заявки медиа-партнеров"""
    return user_id in ALL_ADMIN_IDS

def can_manage_media(user_id):
    """Проверяет, может ли пользователь принимать/отклонять заявки медиа-партнеров"""
    return user_id in ALL_ADMIN_IDS  # Все три админа могут управлять медиа

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [
        [
            InlineKeyboardButton("Moder", callback_data="moder"),
            InlineKeyboardButton("Media", callback_data="media"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = (
        "<b>Приветствуем!</b>\n\n"
        f"Этот бот предназначен для подачи заявок в персонал {PROJECT_NAME}. "
        "Если ты заинтересован в сотрудничестве с проектом VibeMc, и хочешь подать заявку в модераторы - используй команду /moder , "
        "а если хочешь стать медиа-партнером - /media.\n\n"
        "<b>Какая выгода для тебя?</b> За помощь проекту ты сможешь получать: донат-валюту, донат и даже реальные деньги!"
    )
    
    await update.message.reply_text(
        message_text,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "moder":
        await query.edit_message_text(
            "📋 <b>Заявка в модераторы проекта VibeMc</b>\n\n"
            "Чтобы начать процесс подачи заявки, используйте команду /moder",
            parse_mode='HTML'
        )
    elif query.data == "media":
        await query.edit_message_text(
            "🎬 <b>Заявка в медиа-партнеры проекта VibeMc</b>\n\n"
            "Чтобы начать процесс подачи заявки, используйте команду /media",
            parse_mode='HTML'
        )

# ========== АДМИН ПАНЕЛЬ ==========

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /admin для просмотра заявок"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ У вас нет доступа к админ панели")
        return
    
    # Создаем клавиатуру в зависимости от прав
    keyboard = []
    
    if can_view_media(user_id):
        keyboard.append([InlineKeyboardButton("🎬 Media заявки", callback_data="admin_media")])
    
    if can_view_moder(user_id):
        keyboard.append([InlineKeyboardButton("📋 Moder заявки", callback_data="admin_moder")])
    
    if not keyboard:
        await update.message.reply_text("❌ У вас нет прав для просмотра заявок")
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👑 <b>Админ панель</b>\n\n"
        "Выберите тип заявок для просмотра:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок в админ панели"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "admin_moder":
        if not can_view_moder(user_id):
            await query.edit_message_text("❌ У вас нет прав для просмотра заявок модераторов")
            return
        
        # Фильтруем заявки модераторов
        moder_applications = {k: v for k, v in applications.items() if v['type'] == 'moder'}
        
        if not moder_applications:
            await query.edit_message_text("📭 Заявок модераторов нет")
            return
        
        # Отправляем сообщение о количестве заявок
        await query.edit_message_text(f"📋 Найдено {len(moder_applications)} заявок модераторов:")
        
        # Отправляем каждую заявку отдельным сообщением
        for app_id, application in moder_applications.items():
            user_data = application['data']
            
            application_text = (
                f"📋 <b>Заявка модератора #{app_id}</b>\n\n"
                f"👤 <b>Пользователь:</b> {application['first_name']} (@{application['username'] or 'нет'})\n"
                f"🆔 <b>ID:</b> {application['user_id']}\n\n"
                f"🎮 <b>Никнейм:</b> {user_data['nickname']}\n"
                f"💰 <b>Донат:</b> {user_data['donate']}\n"
                f"📛 <b>ФИО:</b> {user_data['fullname']}\n"
                f"📅 <b>Возраст:</b> {user_data['age']}\n"
                f"⏰ <b>Время:</b> {user_data['time']}\n"
                f"💼 <b>Опыт:</b> {user_data['experience']}\n"
                f"📝 <b>О себе:</b> {user_data['about']}\n"
            )
            
            # Кнопки для модерации (только для главного админа)
            keyboard = []
            if can_manage_moder(user_id):
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Принять", callback_data=f"accept_{app_id}"),
                        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{app_id}"),
                    ]
                ]
            else:
                # Для остальных админов показываем сообщение о правах
                application_text += "\n\n⚠️ <i>Только главный администратор может принимать/отклонять заявки модераторов</i>"
            
            reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
            
            await context.bot.send_message(
                chat_id=user_id,
                text=application_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
    
    elif data == "admin_media":
        if not can_view_media(user_id):
            await query.edit_message_text("❌ У вас нет прав для просмотра заявок медиа-партнеров")
            return
        
        # Фильтруем заявки медиа-партнеров
        media_applications = {k: v for k, v in applications.items() if v['type'] == 'media'}
        
        if not media_applications:
            await query.edit_message_text("📭 Заявок медиа-партнеров нет")
            return
        
        # Отправляем сообщение о количестве заявок
        await query.edit_message_text(f"🎬 Найдено {len(media_applications)} заявок медиа-партнеров:")
        
        # Отправляем каждую заявку отдельным сообщением
        for app_id, application in media_applications.items():
            user_data = application['data']
            
            application_text = (
                f"🎬 <b>Заявка медиа-партнера #{app_id}</b>\n\n"
                f"👤 <b>Пользователь:</b> {application['first_name']} (@{application['username'] or 'нет'})\n"
                f"🆔 <b>ID:</b> {application['user_id']}\n\n"
                f"🎮 <b>Никнейм:</b> {user_data['nickname']}\n"
                f"📛 <b>ФИО:</b> {user_data['fullname']}\n"
                f"📅 <b>Возраст:</b> {user_data['age']}\n"
                f"📺 <b>Площадка:</b> {user_data['platform']}\n"
                f"📊 <b>Статистика:</b> {user_data['stats']}\n"
                f"📝 <b>О себе:</b> {user_data['about']}\n"
                f"🔗 <b>Ссылки:</b> {user_data['links']}\n"
            )
            
            # Кнопки для модерации (все админы могут управлять медиа)
            keyboard = [
                [
                    InlineKeyboardButton("✅ Принять", callback_data=f"accept_{app_id}"),
                    InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{app_id}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=user_id,
                text=application_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )

# ========== ОБРАБОТЧИКИ ДЛЯ МОДЕРАТОРОВ ==========

async def moder_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс подачи заявки в модераторы"""
    context.user_data['moder_application'] = {}
    
    await update.message.reply_text(
        "📋 <b>Заявка в модераторы проекта VibeMc</b>\n\n"
        "Давайте заполним заявку. Пожалуйста, отвечайте на вопросы по порядку.\n\n"
        "<b>Вопрос 1 из 7:</b> Ваш никнейм?",
        parse_mode='HTML'
    )
    return MODER_NICKNAME

async def moder_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет никнейм и запрашивает донат"""
    context.user_data['moder_application']['nickname'] = update.message.text
    
    await update.message.reply_text(
        "<b>Вопрос 2 из 7:</b> Ваш донат?",
        parse_mode='HTML'
    )
    return MODER_DONATE

async def moder_donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет донат и запрашивает ФИО"""
    context.user_data['moder_application']['donate'] = update.message.text
    
    await update.message.reply_text(
        "<b>Вопрос 3 из 7:</b> Ваше ФИО?",
        parse_mode='HTML'
    )
    return MODER_FULLNAME

async def moder_fullname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет ФИО и запрашивает возраст"""
    context.user_data['moder_application']['fullname'] = update.message.text
    
    await update.message.reply_text(
        "<b>Вопрос 4 из 7:</b> Ваш возраст?",
        parse_mode='HTML'
    )
    return MODER_AGE

async def moder_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет возраст и запрашивает время"""
    context.user_data['moder_application']['age'] = update.message.text
    
    await update.message.reply_text(
        "<b>Вопрос 5 из 7:</b> Сколько часов готовы уделять проекту?",
        parse_mode='HTML'
    )
    return MODER_TIME

async def moder_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет время и запрашивает опыт"""
    context.user_data['moder_application']['time'] = update.message.text
    
    await update.message.reply_text(
        "<b>Вопрос 6 из 7:</b> Был ли опыт у вас в этой сфере?",
        parse_mode='HTML'
    )
    return MODER_EXPERIENCE

async def moder_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет опыт и запрашивает информацию о себе"""
    context.user_data['moder_application']['experience'] = update.message.text
    
    await update.message.reply_text(
        "<b>Вопрос 7 из 7:</b> Расскажите о себе.",
        parse_mode='HTML'
    )
    return MODER_ABOUT

async def moder_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет информацию о себе и завершает заявку"""
    global application_counter
    
    context.user_data['moder_application']['about'] = update.message.text
    user_data = context.user_data['moder_application']
    user = update.effective_user
    
    # Сохраняем заявку
    application_id = application_counter
    application_counter += 1
    
    applications[application_id] = {
        'type': 'moder',
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'data': user_data.copy()
    }
    
    # Сохраняем в файл
    save_applications()
    
    # Сообщение пользователю
    await update.message.reply_text(
        "✅ <b>Заявка в модераторы завершена!</b>\n\n"
        "Ваши данные:\n"
        f"Никнейм: {user_data['nickname']}\n"
        f"Донат: {user_data['donate']}\n"
        f"ФИО: {user_data['fullname']}\n"
        f"Возраст: {user_data['age']}\n"
        f"Время: {user_data['time']}\n"
        f"Опыт: {user_data['experience']}\n"
        f"О себе: {user_data['about']}\n\n"
        "Спасибо за заявку! Мы рассмотрим её в ближайшее время.",
        parse_mode='HTML'
    )
    
    context.user_data.pop('moder_application', None)
    return ConversationHandler.END

# ========== ОБРАБОТЧИКИ ДЛЯ МЕДИА-ПАРТНЕРОВ ==========

async def media_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс подачи заявки в медиа-партнеры"""
    context.user_data['media_application'] = {}
    
    await update.message.reply_text(
        "🎬 <b>Заявка в медиа-партнеры проекта VibeMc</b>\n\n"
        "Давайте заполним заявку. Пожалуйста, отвечайте на вопросы по порядку.\n\n"
        "<b>Вопрос 1 из 7:</b> Ваш никнейм?",
        parse_mode='HTML'
    )
    return MEDIA_NICKNAME

async def media_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет никнейм и запрашивает ФИО"""
    context.user_data['media_application']['nickname'] = update.message.text
    
    await update.message.reply_text(
        "<b>Вопрос 2 из 7:</b> Ваше ФИО?",
        parse_mode='HTML'
    )
    return MEDIA_FULLNAME

async def media_fullname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет ФИО и запрашивает возраст"""
    context.user_data['media_application']['fullname'] = update.message.text
    
    await update.message.reply_text(
        "<b>Вопрос 3 из 7:</b> Ваш возраст?",
        parse_mode='HTML'
    )
    return MEDIA_AGE

async def media_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет возраст и запрашивает площадку"""
    context.user_data['media_application']['age'] = update.message.text
    
    await update.message.reply_text(
        "<b>Вопрос 4 из 7:</b> На какой площадке снимаете?",
        parse_mode='HTML'
    )
    return MEDIA_PLATFORM

async def media_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет площадку и запрашивает статистику"""
    context.user_data['media_application']['platform'] = update.message.text
    
    await update.message.reply_text(
        "<b>Вопрос 5 из 7:</b> Сколько у вас подписчиков, просмотров в среднем?",
        parse_mode='HTML'
    )
    return MEDIA_STATS

async def media_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет статистику и запрашивает информацию о себе"""
    context.user_data['media_application']['stats'] = update.message.text
    
    await update.message.reply_text(
        "<b>Вопрос 6 из 7:</b> Расскажите немного о себе.",
        parse_mode='HTML'
    )
    return MEDIA_ABOUT

async def media_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет информацию о себе и запрашивает ссылки"""
    context.user_data['media_application']['about'] = update.message.text
    
    await update.message.reply_text(
        "<b>Вопрос 7 из 7:</b> Прикрепите ссылку на ваш канал, а также скриншот из студии.\n\n"
        "<i>Примечание: Если хотите отправить скриншот, отправьте его следующим сообщением после текста с ссылками.</i>",
        parse_mode='HTML'
    )
    return MEDIA_LINKS

async def media_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет ссылки и завершает заявку"""
    global application_counter
    
    context.user_data['media_application']['links'] = update.message.text
    user_data = context.user_data['media_application']
    user = update.effective_user
    
    # Сохраняем заявку
    application_id = application_counter
    application_counter += 1
    
    applications[application_id] = {
        'type': 'media',
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'data': user_data.copy()
    }
    
    # Сохраняем в файл
    save_applications()
    
    # Сообщение пользователю
    await update.message.reply_text(
        "✅ <b>Заявка в медиа-партнеры завершена!</b>\n\n"
        "Ваши данные:\n"
        f"Никнейм: {user_data['nickname']}\n"
        f"ФИО: {user_data['fullname']}\n"
        f"Возраст: {user_data['age']}\n"
        f"Площадка: {user_data['platform']}\n"
        f"Статистика: {user_data['stats']}\n"
        f"О себе: {user_data['about']}\n"
        f"Ссылки: {user_data['links']}\n\n"
        "Спасибо за заявку! Мы рассмотрим её в ближайшее время.",
        parse_mode='HTML'
    )
    
    context.user_data.pop('media_application', None)
    return ConversationHandler.END

# ========== ОБРАБОТКА КНОПОК ПРИНЯТЬ/ОТКЛОНИТЬ ==========

async def handle_application_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка действий с заявками (принять/отклонить)"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    action, application_id = data.split('_')
    application_id = int(application_id)
    
    # Проверяем существование заявки
    if application_id not in applications:
        await query.edit_message_text("⚠️ Заявка не найдена или уже обработана")
        return
    
    application = applications[application_id]
    
    # Проверяем права пользователя в зависимости от типа заявки
    if application['type'] == 'moder':
        if not can_manage_moder(user_id):
            await query.answer("❌ У вас нет прав для управления заявками модераторов", show_alert=True)
            return
    elif application['type'] == 'media':
        if not can_manage_media(user_id):
            await query.answer("❌ У вас нет прав для управления заявками медиа-партнеров", show_alert=True)
            return
    
    user_id_applicant = application['user_id']
    
    if action == "accept":
        # Обновляем сообщение с заявкой
        new_text = query.message.text + "\n\n✅ <b>ЗАЯВКА ПРИНЯТА</b>"
        await query.edit_message_text(
            new_text,
            parse_mode='HTML'
        )
        
        # Уведомляем пользователя
        try:
            await context.bot.send_message(
                chat_id=user_id_applicant,
                text="🎉 <b>Поздравляем! Ваша заявка принята!</b>\n\n"
                     "С вами свяжется наш менеджер в ближайшее время для обсуждения деталей сотрудничества.",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя {user_id_applicant}: {e}")
        
        # Удаляем заявку из хранилища
        del applications[application_id]
        save_applications()  # Сохраняем изменения
        
    elif action == "reject":
        # Сохраняем ID заявки для запроса причины
        context.user_data['reject_application_id'] = application_id
        context.user_data['reject_message_id'] = query.message.message_id
        context.user_data['reject_chat_id'] = query.message.chat.id
        context.user_data['reject_message_text'] = query.message.text
        
        # Запрашиваем причину отклонения
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="📝 <b>Укажите причину отклонения заявки:</b>",
            parse_mode='HTML'
        )
        
        return REJECT_REASON

async def handle_reject_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка причины отклонения заявки"""
    reason = update.message.text
    application_id = context.user_data.get('reject_application_id')
    
    if application_id not in applications:
        await update.message.reply_text("⚠️ Заявка не найдена")
        context.user_data.pop('reject_application_id', None)
        return ConversationHandler.END
    
    application = applications[application_id]
    user_id = application['user_id']
    
    # Обновляем сообщение с заявкой
    message_id = context.user_data.get('reject_message_id')
    chat_id = context.user_data.get('reject_chat_id')
    original_text = context.user_data.get('reject_message_text')
    
    new_text = original_text + f"\n\n❌ <b>ЗАЯВКА ОТКЛОНЕНА</b>\nПричина: {reason}"
    
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=new_text,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Не удалось обновить сообщение: {e}")
    
    # Уведомляем пользователя
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ <b>Ваша заявка не была принята</b>\n\n"
                 f"Причина: {reason}\n\n"
                 "Попробуйте еще раз через 14 календарных суток.",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить пользователя {user_id}: {e}")
    
    # Удаляем заявку из хранилища
    del applications[application_id]
    save_applications()  # Сохраняем изменения
    
    # Очищаем временные данные
    context.user_data.pop('reject_application_id', None)
    context.user_data.pop('reject_message_id', None)
    context.user_data.pop('reject_chat_id', None)
    context.user_data.pop('reject_message_text', None)
    
    await update.message.reply_text("✅ Пользователь уведомлен об отклонении заявки")
    
    return ConversationHandler.END

# ========== ОБЩИЕ ФУНКЦИИ ==========

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет диалог подачи заявки"""
    if 'moder_application' in context.user_data:
        context.user_data.pop('moder_application')
    if 'media_application' in context.user_data:
        context.user_data.pop('media_application')
    if 'reject_application_id' in context.user_data:
        context.user_data.pop('reject_application_id')
    
    await update.message.reply_text(
        "Заявка отменена. Если захотите подать заявку снова, используйте /moder или /media"
    )
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "ℹ️ <b>Помощь по боту</b>\n\n"
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/moder - Подать заявку в модераторы\n"
        "/media - Подать заявку в медиа-партнеры\n"
        "/admin - Админ панель (только для администраторов)\n"
        "/cancel - Отменить текущую заявку\n\n"
        "По всем вопросам обращайтесь к администрации.",
        parse_mode='HTML'
    )

def main():
    """Основная функция запуска бота"""
    # Загружаем заявки при старте
    load_applications()
    
    application = Application.builder().token(TOKEN).build()
    
    # Обработчик команды /cancel ДО всех остальных
    application.add_handler(CommandHandler("cancel", cancel))
    
    # Обработчики простых команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_command))
    
    # Обработчики кнопок
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(moder|media)$"))
    application.add_handler(CallbackQueryHandler(admin_button_handler, pattern="^admin_(moder|media)$"))
    application.add_handler(CallbackQueryHandler(handle_application_action, pattern=r"^(accept|reject)_\d+$"))
    
    # Настройка ConversationHandler для модераторов
    moder_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("moder", moder_start)],
        states={
            MODER_NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, moder_nickname)],
            MODER_DONATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, moder_donate)],
            MODER_FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, moder_fullname)],
            MODER_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, moder_age)],
            MODER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, moder_time)],
            MODER_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, moder_experience)],
            MODER_ABOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, moder_about)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Настройка ConversationHandler для медиа-партнеров
    media_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("media", media_start)],
        states={
            MEDIA_NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, media_nickname)],
            MEDIA_FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, media_fullname)],
            MEDIA_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, media_age)],
            MEDIA_PLATFORM: [MessageHandler(filters.TEXT & ~filters.COMMAND, media_platform)],
            MEDIA_STATS: [MessageHandler(filters.TEXT & ~filters.COMMAND, media_stats)],
            MEDIA_ABOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, media_about)],
            MEDIA_LINKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, media_links)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Настройка ConversationHandler для отклонения заявок
    reject_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reject_reason)],
        states={
            REJECT_REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reject_reason)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Добавляем обработчики бесед ПОСЛЕДНИМИ
    application.add_handler(moder_conv_handler)
    application.add_handler(media_conv_handler)
    application.add_handler(reject_conv_handler)
    
    # Запускаем бота
    print("Бот запущен!")
    logger.info("Бот успешно запущен")
    
    # Простой запуск через polling
    application.run_polling()

if __name__ == "__main__":
    main()
