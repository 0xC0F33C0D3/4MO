from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from database.crud import create_user
from database.database import SessionLocal

def register(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, choose_role))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [["Заказчик", "Исполнитель"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text("Привет! Выбери свою роль:", reply_markup=reply_markup)

def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    role = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Unknown"
    
    if role not in ["Заказчик", "Исполнитель"]:
        update.message.reply_text("Пожалуйста, выбери роль, используя кнопки.")
        return
    
    db = SessionLocal()
    create_user(db, username, role)
    db.close()
    
    update.message.reply_text(f"Вы зарегистрированы как {role}!")
