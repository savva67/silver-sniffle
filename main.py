import asyncio
import random
from typing import Optional
from datetime import datetime
import logging

from telegram import Update, ChatPermissions, ChatMember
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего бота
BOT_TOKEN = "7245379721:AAG_5q9hPGHdQwSFH5f0jw0NsmauKajyKsI"

# Команда /random - выбирает случайного участника
async def random_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        message = update.effective_message
        
        # Отправляем сообщение о начале поиска
        status_message = await message.reply_text("🔍 *ищу участников...*", parse_mode=ParseMode.MARKDOWN)
        
        # Получаем администраторов чата (всегда доступно)
        admins = await context.bot.get_chat_administrators(chat_id)
        
        # Собираем всех участников через администраторов
        # (это не идеально, но работает без прав админа)
        members = []
        
        for admin in admins:
            if not admin.user.is_bot and admin.user not in members:
                members.append(admin.user)
        
        # Также пробуем получить участников через историю сообщений (если есть)
        try:
            # Получаем последние сообщения для поиска участников
            async for msg in context.bot.get_chat_history(chat_id, limit=100):
                if msg.from_user and not msg.from_user.is_bot:
                    if msg.from_user not in members:
                        members.append(msg.from_user)
        except:
            pass  # игнорируем ошибки при получении истории
        
        if not members:
            await status_message.edit_text(
                "❌ *не удалось найти участников*\n"
                "убедитесь, что в чате есть активные пользователи",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Выбираем случайного участника
        chosen_one = random.choice(members)
        
        # Форматируем упоминание
        if chosen_one.username:
            mention = f"@{chosen_one.username}"
        else:
            mention = f"[{chosen_one.first_name}](tg://user?id={chosen_one.id})"
        
        # Удаляем статусное сообщение
        await status_message.delete()
        
        # Отправляем результат
        await message.reply_text(
            f"🎲 *боги рандома выбрали:*\n"
            f"└ {mention}\n\n"
            f"*участников в списке:* {len(members)}",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"ошибка в команде /random: {e}")
        await update.message.reply_text(
            "❌ *ошибка при выборе участника*\n"
            "попробуйте позже или сделайте бота администратором",
            parse_mode=ParseMode.MARKDOWN
        )

# Команда /all - отмечает всех участников
async def mention_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        message = update.effective_message
        
        # Проверяем, является ли бот администратором
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        
        if bot_member.status not in ["administrator", "creator"]:
            await message.reply_text(
                "⚠️ *ботам нужны права администратора*\n"
                "для отметки всех участников сделайте меня администратором!\n\n"
                "*нужные права:*\n"
                "• Чтение сообщений\n"
                "• Удаление сообщений (опционально)",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Отправляем сообщение о начале
        status_message = await message.reply_text(
            "🔄 *собираю участников...*",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Получаем всех участников чата
        members = []
        members_count = 0
        
        try:
            # Пытаемся получить всех участников (только для админов)
            async for member in context.bot.get_chat_members(chat_id):
                user = member.user
                if not user.is_bot:
                    members.append(user)
                    members_count += 1
                    
                    # Ограничим количество, чтобы не спамить
                    if members_count >= 100:
                        break
                        
        except Exception as e:
            logger.error(f"Ошибка при получении участников: {e}")
            await status_message.edit_text(
                "❌ *ошибка доступа к списку участников*\n"
                "проверьте права бота",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        if not members:
            await status_message.edit_text(
                "❌ *не найдено участников для отметки*",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Обновляем статус
        await status_message.edit_text(
            f"📝 *найдено участников:* {len(members)}\n"
            f"✍️ *подготавливаю упоминания...*",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Формируем упоминания
        mentions = []
        for user in members:
            if user.username:
                mentions.append(f"@{user.username}")
            else:
                mentions.append(f"[{user.first_name}](tg://user?id={user.id})")
        
        # Отправляем небольшими группами
        chunk_size = 30  # Безопасное количество
        chunks = [mentions[i:i + chunk_size] for i in range(0, len(mentions), chunk_size)]
        
        # Удаляем статусное сообщение
        await status_message.delete()
        
        # Отправляем заголовок
        await message.reply_text(
            f"📢 *ВНИМАНИЕ ВСЕМ ЧАТОМ!* 📢\n"
            f"─────────────────────\n"
            f"*всего участников:* {len(members)}\n"
            f"*частей:* {len(chunks)}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Отправляем упоминания частями
        for i, chunk in enumerate(chunks):
            mention_text = " ".join(chunk)  # Используем пробелы для компактности
            
            await message.reply_text(
                f"📢 *часть {i + 1}/{len(chunks)}*\n"
                f"{mention_text}",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Небольшая задержка между сообщениями
            await asyncio.sleep(1)
        
        # Финальное сообщение
        await message.reply_text(
            f"✅ *готово!*\n"
            f"отмечено {len(members)} участников",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"ошибка в команде /all: {e}")
        await update.message.reply_text(
            "❌ *произошла ошибка*\n"
            "попробуйте позже",
            parse_mode=ParseMode.MARKDOWN
        )

# Команда /help - справка по боту
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *бот-рандомайзер и упоминатель*\n\n"
        "*доступные команды:*\n"
        "• /random - выбрать случайного участника\n"
        "• /all - отметить всех участников\n"
        "• /help - показать справку\n\n"
        "*важно:*\n"
        "• для /all нужны права администратора\n"
        "• для /random права не обязательны, но улучшают работу"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

# Команда /start - приветствие
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 *привет! я - бот для рандома и отметок*\n\n"
        "используй /help для списка команд"
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

# Обработка ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ *произошла ошибка*\n"
            "проверьте логи или попробуйте позже",
            parse_mode=ParseMode.MARKDOWN
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
    print("🤖 Бот запущен...")
    print("📝 Проверьте, что бот является администратором чата для полной функциональности")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
