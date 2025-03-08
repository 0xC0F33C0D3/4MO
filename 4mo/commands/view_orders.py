from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from database.database import SessionLocal
from database.crud import get_orders, get_user

async def view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    db = SessionLocal()
    user = get_user(db, user_id)

    if not user or user.user_type != "Исполнитель":
        await update.message.reply_text("❌ Только исполнители могут просматривать заказы.")
        db.close()
        return

    orders = get_orders(db)
    
    # Показываем только заказы, которые еще не взяты в работу
    available_orders = [o for o in orders if o.status == "Ожидает выполнения"]
    db.close()

    if not available_orders:
        await update.message.reply_text("🔍 Сейчас нет доступных заказов.")
        return

    response = "📜 Доступные заказы:\n\n"
    for order in available_orders:
        response += f"📌 {order.description}\n📎 ID: {order.id}\n\n"
    
    await update.message.reply_text(response)

# Регистрация команды
#def register(application):
   # application.add_handler(MessageHandler(filters.Regex("^🔍 Посмотреть доступные заказы$"), view_orders))
