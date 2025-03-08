from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
from database.database import SessionLocal
from database.crud import get_user, create_user
from commands.menu import get_customer_keyboard, get_executor_keyboard

# Этапы диалога
CHOOSE_ROLE = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    db = SessionLocal()
    user = get_user(db, user_id)
    db.close()

    if user:
        reply_markup = get_customer_keyboard() if user.user_type == "Заказчик" else get_executor_keyboard()
        await update.message.reply_text("Вы уже зарегистрированы. Ваше меню:", reply_markup=reply_markup)
        return ConversationHandler.END

    keyboard = [["Заказчик", "Исполнитель"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Привет! Выбери свою роль:", reply_markup=reply_markup)

    return CHOOSE_ROLE  # Переход на этап ожидания выбора роли

async def choose_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    role = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Nobody"

    if role not in ["Заказчик", "Исполнитель"]:
        await update.message.reply_text("Пожалуйста, выбери роль, используя кнопки.")
        return CHOOSE_ROLE  # Остаемся в этом этапе

    db = SessionLocal()
    user = create_user(db,user_id,username,role)
    db.close()

    reply_markup = get_customer_keyboard() if role == "Заказчик" else get_executor_keyboard()
    await update.message.reply_text(f"Вы зарегистрированы как {role}!", reply_markup=reply_markup)

    return ConversationHandler.END  # Выход из режима ожидания

async def change_role(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [["Заказчик", "Исполнитель"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выберите новую роль:", reply_markup=reply_markup)
    return CHOOSE_ROLE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Регистрация отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def register(application):
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={CHOOSE_ROLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_role)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
    application.add_handler(CommandHandler("change_role", change_role))
