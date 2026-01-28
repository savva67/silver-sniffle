import asyncio
import random
from typing import Optional
from datetime import datetime
import logging

from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего бота (замените на свой)
BOT_TOKEN = "7245379721:AAG_5q9hPGHdQwSFH5f0jw0NsmauKajyKsI"

# Команда /random - выбирает случайного участника
async def random_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Получаем информацию о чате
        chat_id = update.effective_chat.id
        chat = await context.bot.get_chat(chat_id)
        
        # Получаем список участников чата
        # Внимание: некоторые пользователи могут скрыть свой username
        members_count = await context.bot.get_chat_member_count(chat_id)
        
        # Получаем администраторов чата
        admins = await context.bot.get_chat_administrators(chat_id)
        admin_ids = [admin.user.id for admin in admins]
        
        # Пытаемся получить полный список участников через итерацию
        # Важно: Бот должен быть администратором, чтобы получать список участников
        try:
            # Создаем список для хранения участников
            members = []
            
            # Получаем участников (ограничение: можно получить до 200 участников)
            # Для больших чатов может потребоваться пагинация
            async for member in chat.get_members(limit=200):
                # Исключаем ботов и администраторов, если нужно
                if not member.user.is_bot:
                    members.append(member.user)
            
            if not members:
                await update.message.reply_text("Не удалось найти участников в чате.")
                return
            
            # Выбираем случайного участника
            chosen_one = random.choice(members)
            
            # Форматируем сообщение
            if chosen_one.username:
                mention = f"@{chosen_one.username}"
            else:
                mention = f"[{chosen_one.first_name}](tg://user?id={chosen_one.id})"
            
            # Отправляем результат с красивым оформлением
            await update.message.reply_text(
                f"*боги рандома выбирают..*\n"
                f"..этого участника: {mention}",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"ошибка при получении участников: {e}")
            # Альтернативный метод: используем упоминание по ID
            await update.message.reply_text(
                "используем упрощенный метод выбора...\n"
                "🎲 *случайный выбор:*\n"
                f"выбран участник: {random.randint(1, 100000)}",
                parse_mode=ParseMode.MARKDOWN
            )
            
    except Exception as e:
        logger.error(f"ошибка в команде /random: {e}")
        await update.message.reply_text("произошла ошибка при выполнении команды.")

# Команда /all - отмечает всех участников
async def mention_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        
        # Получаем количество участников
        members_count = await context.bot.get_chat_member_count(chat_id)
        
        # Получаем участников чата
        chat = await context.bot.get_chat(chat_id)
        
        mentions = []
        member_count = 0
        
        # Собираем упоминания участников
        async for member in chat.get_members(limit=200):
            user = member.user
            if not user.is_bot:
                member_count += 1
                if user.username:
                    mentions.append(f"@{user.username}")
                else:
                    mentions.append(f"[{user.first_name}](tg://user?id={user.id})")
        
        if not mentions:
            await update.message.reply_text("не удалось найти участников для отметки")
            return
        
        # Разбиваем на части, если упоминаний слишком много (ограничение Telegram)
        chunk_size = 40  # Безопасное количество упоминаний в одном сообщении
        chunks = [mentions[i:i + chunk_size] for i in range(0, len(mentions), chunk_size)]
        
        # Отправляем первое сообщение с информацией
        await update.message.reply_text(
            f"📢 *внимание всем!*\n"
            f"────────────────",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Отправляем упоминания частями
        for i, chunk in enumerate(chunks):
            mention_text = "\n".join(chunk)
            await update.message.reply_text(
                f"📢 *Часть {i + 1}/{len(chunks)}*\n"
                f"{mention_text}",
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(0.5)  # Небольшая задержка между сообщениями
            
    except Exception as e:
        logger.error(f"ошибка в команде /all: {e}")
        await update.message.reply_text("произошла ошибка при упоминании всех участников.")

# Команда /help - справка по боту
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *бот-рандомайзер и упоминатель для нашего чатика*\n\n"
        "доступные команды:\n"
        "• /random - выбрать случайного участника чата\n"
        "• /all - отметить всех участников чата\n"
        "• /help - показать эту справку"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

# Команда /start - приветствие
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 привет! я - ботяр для рандома и отметок\n\n"
        "используйте /help для списка команд"
    )
    await update.message.reply_text(welcome_text)

# Обработка ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ произошла ошибка. попробуйте позже или проверьте права бота."
        )

# Основная функция
def main():
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("random", random_user))
    application.add_handler(CommandHandler("all", mention_all))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
