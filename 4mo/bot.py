# bot.py
import logging
from telegram.ext import ApplicationBuilder
from database.database import init_db
from commands import register_commands

init_db()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    application = ApplicationBuilder().token("7627069430:AAGRuYOXM6G23_pcCj1RLvpHu4mqwpTIkMY").build()  # Замените YOUR_BOT_TOKEN на ваш токен

    # Регистрируем команды
    register_commands(application)

    logger.info("Бот запущен")
    application.run_polling()

if __name__ == "__main__":
    main()  # Запуск бота