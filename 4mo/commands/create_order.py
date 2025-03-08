from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database.database import SessionLocal
from database.crud import create_order, get_user

# Состояния для диалога
ENTER_DESCRIPTION = 1

# Начинаем процесс создания заказа
async def start_order_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    db = SessionLocal()
    user = get_user(db, user_id)
    db.close()

    if not user or user.user_type != "Заказчик":
        await update.message.reply_text("❌ Только заказчики могут размещать заказы.")
        return ConversationHandler.END

    await update.message.reply_text("✏️ Введите описание заказа:", reply_markup=ReplyKeyboardRemove())
    return ENTER_DESCRIPTION

# Пользователь вводит описание заказа
async def enter_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    description = update.message.text

    db = SessionLocal()
    user = get_user(db, user_id)
    
    if not user:
        await update.message.reply_text("❌ Ошибка: Пользователь не найден.")
        db.close()
        return ConversationHandler.END

    create_order(db, description, user.id)
    db.close()

    await update.message.reply_text("✅ Заказ успешно создан! Он теперь доступен исполнителям.")
    return ConversationHandler.END

# Обработчик отмены
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Создание заказа отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Регистрация обработчиков
def register(application):
    application.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📌 Разместить заказ$"), start_order_creation)],
        states={ENTER_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_description)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
