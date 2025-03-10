from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters
from database.database import SessionLocal
from database.crud import get_active_executors, get_user, create_order
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def show_active_executors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список активных исполнителей."""
    db = SessionLocal()
    executors = get_active_executors(db)
    db.close()

    if not executors:
        await update.message.reply_text("❌ Сейчас нет активных исполнителей.")
        return

    response = "🟢 Доступные исполнители:\n\n"
    keyboard = []

    for executor in executors:
        response += f"👤 @{executor.username} | ⭐ {executor.rating:.1f} | 📎 ID: {executor.id}\n"
        keyboard.append([f"👤 {executor.username} (ID: {executor.id})"])

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(response + "\nВыберите исполнителя:", reply_markup=reply_markup)

async def propose_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Заказчик предлагает заказ исполнителю."""
    text = update.message.text
    executor_id = int(text.split("ID: ")[1].strip(")"))

    context.user_data["selected_executor_id"] = executor_id
    await update.message.reply_text("✏️ Введите описание заказа:")

    return 1  # Ожидание ввода описания

async def send_order_to_executor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создает заказ и отправляет предложение исполнителю."""
    description = update.message.text
    customer_id = update.message.from_user.id
    executor_id = context.user_data["selected_executor_id"]

    db = SessionLocal()
    order = create_order(db, description, customer_id, executor_id)
    db.close()

    await update.message.reply_text(f"✅ Заказ ID {order.id} отправлен исполнителю!")

    # Отправляем уведомление исполнителю
    executor = get_user(db, executor_id)
    if executor:
        await context.bot.send_message(chat_id=executor.telegram_id, text=f"📌 Вам предложен заказ: {description}\n✅ Принять / ❌ Отклонить")

def register(application):
    application.add_handler(MessageHandler(filters.Regex("^👤 .* \\(ID: .*\\)$"), propose_order))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_order_to_executor))
