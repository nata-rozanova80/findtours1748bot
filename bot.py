from telegram.ext import ApplicationBuilder, CommandHandler
from config import TELEGRAM_TOKEN
from db import init_db, get_last_offers

async def start(update, context):
    await update.message.reply_text(
        "Привет! Я бот-парсер горящих туров.\n"
        "Набери /promo, чтобы получить актуальные предложения."
    )

async def promo(update, context):
    offers = get_last_offers(limit=10)
    if not offers:
        await update.message.reply_text(
            "Сейчас нет сохранённых предложений.\n"
            "Попробуйте /promo чуть позже."
        )
        return

    lines = []
    for i, (title, link, source, created_at) in enumerate(offers, start=1):
        lines.append(f"{i}. {title}\n{link}")
    await update.message.reply_text("\n\n".join(lines))

def main():
    init_db()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("promo", promo))
    app.run_polling()

if __name__ == "__main__":
    main()
