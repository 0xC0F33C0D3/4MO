from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from database.database import SessionLocal
from database.crud import get_user

# Функция для создания клавиатуры заказчика
def get_customer_keyboard():
    keyboard = [
        ["📌 Разместить заказ"],
        ["ℹ️ Информация об аккаунте"],
        ["📜 История заказов"],
        ["💰 Пополнить баланс"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_executor_keyboard():
    keyboard = [
        ["✅ Выйти на линию"],
        ["📜 История заказов"],
        ["ℹ️ Информация об аккаунте"],
        ["🔍 Посмотреть доступные заказы"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    db = SessionLocal()
    user = get_user(db, user_id)
    db.close()

    if not user:
        await update.message.reply_text("Вы не зарегистрированы. Введите /start, чтобы выбрать роль.")
        return

    if user.user_type == "Заказчик":
        reply_markup = get_customer_keyboard()
        await update.message.reply_text("📋 Главное меню:", reply_markup=reply_markup)
    else:
        reply_markup = get_executor_keyboard()
        await update.message.reply_text("📋 Главное меню:", reply_markup=reply_markup)

# Регистрация команды в боте
def register(application):
    application.add_handler(CommandHandler("menu", menu))
