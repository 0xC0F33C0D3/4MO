# bot.py
import logging
from telegram.ext import ApplicationBuilder
from database.database import init_db
from commands import register_commands
from dotenv import load_dotenv
import os

load_dotenv()
init_db()
BOT_TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print(BOT_TOKEN)
    application = ApplicationBuilder().token(BOT_TOKEN).build()  # Замените YOUR_BOT_TOKEN на ваш токен

    # Регистрируем команды
    register_commands(application)

    logger.info("Бот запущен")
    application.run_polling()

if __name__ == "__main__":
    main()  # Запуск бота