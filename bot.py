from telegram.ext import ApplicationBuilder, CommandHandler
from config import TELEGRAM_TOKEN
from db import init_db, get_last_offers
from utils import setup_logging
import logging

logger = logging.getLogger(__name__)

async def start(update, context):
    await update.message.reply_text(
        "Привет! Я бот-парсер горящих туров.\n"
        "Набери /promo, чтобы получить актуальные предложения."
    )

async def promo(update, context):
    user = update.effective_user
    logger.info("Пользователь %s (%s) вызвал /promo", user.id, user.username)

    try:
        offers = get_last_offers(limit=10)
        logger.info("get_last_offers вернул %d записей", len(offers))
    except Exception as e:
        logger.exception("Ошибка при чтении БД в /promo: %s", e)
        await update.message.reply_text(
            "Ой, у меня временные проблемы с базой данных.\n"
            "Попробуйте ещё раз через пару минут."
        )
        return

    if not offers:
        logger.warning("В БД нет предложений для выдачи пользователю %s", user.id)
        await update.message.reply_text(
            "Сейчас нет сохранённых предложений.\n"
            "Попробуйте /promo чуть позже."
        )
        return

    lines = []
    for i, (title, link, source, created_at) in enumerate(offers, start=1):
        logger.debug("Предложение #%d: %s (%s)", i, title, link)
        lines.append(f"{i}. {title}\n{link}")
    await update.message.reply_text("\n\n".join(lines))

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Бот запускается")

    init_db()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("promo", promo))
    logger.info("Хендлеры зарегистрированы, запускаем polling")
    app.run_polling()

if __name__ == "__main__":
    main()
