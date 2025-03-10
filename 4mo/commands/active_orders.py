from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from database.database import SessionLocal
from database.crud import get_user, get_active_orders_for_executor, get_unfinished_orders_for_customer


async def active_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    db = SessionLocal()
    user = get_user(db, user_id)

    if not user:
        await update.message.reply_text("❌ Вы не зарегистрированы.")
        db.close()
        return

    if user.user_type == "Исполнитель":
        orders = get_active_orders_for_executor(db, user.id)
    else:
        orders = get_unfinished_orders_for_customer(db, user.id)

    db.close()

    if not orders:
        await update.message.reply_text("📂 У вас нет активных заказов.")
        return

    response = "📂 Ваши активные заказы:\n\n"
    for order in orders:
        response += f"📌 {order.description}\n📎 ID: {order.id} | Статус: {order.status}\n\n"
    
    await update.message.reply_text(response)

# Регистрация команды
def register(application):
    application.add_handler(MessageHandler(filters.Regex("^📂 Активные заказы$"), active_orders))
