# bot.py
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from config import TELEGRAM_TOKEN
from db import init_db, get_last_offers
from utils import setup_logging
from parser import update_offers_from_all_sources

logger = logging.getLogger(__name__)


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Я бот-парсер горящих туров.\n"
        "Собираю спецпредложения с сайтов Tez-tour и 1001-tours, "
        "сохраняю их в базу и по команде /promo показываю "
        "до 10 актуальных туров с ссылками."
    )
    await update.message.reply_text(text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-парсер горящих туров.\n"
        "Набери /promo, чтобы получить актуальные предложения."
    )


async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Список команд:\n"
        "/start - Приветствие и краткая инструкция\n"
        "/promo - Показать до 10 актуальных туров\n"
        "/update - Обновить базу туров (запуск парсера)\n"
        "/stats - Статистика по базе туров\n"
        "/about - Информация о боте"
    )
    await update.message.reply_text(text)


async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Запускаю обновление базы туров, подождите...")
    try:
        new_count = update_offers_from_all_sources()
        await update.message.reply_text(
            f"Обновление завершено. Добавлено новых предложений: {new_count}."
        )
    except Exception as e:
        logger.exception("Ошибка при обновлении базы в /update: %s", e)
        await update.message.reply_text(
            "Произошла ошибка при обновлении базы. Попробуйте позже."
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # временный вариант — считаем количество записей по get_last_offers
        offers = get_last_offers(limit=1000)
        total_offers = len(offers)
        text = (
            "Статистика по базе туров:\n"
            f"Всего предложений (по последнему выбору): {total_offers}\n"
            "Подробная статистика по источникам будет добавлена позже."
        )
    except Exception as e:
        logger.exception("Ошибка при получении статистики в /stats: %s", e)
        text = "Не удалось получить статистику по базе. Попробуйте позже."
    await update.message.reply_text(text)


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Бот запускается")

    init_db()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("promo", promo))
    app.add_handler(CommandHandler("about", about_command))

    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("update", update_command))
    app.add_handler(CommandHandler("stats", stats_command))

    logger.info("Хендлеры зарегистрированы, запускаем polling")
    app.run_polling()


if __name__ == "__main__":
    main()
