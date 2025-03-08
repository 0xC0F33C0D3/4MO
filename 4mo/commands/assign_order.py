from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database.database import SessionLocal
from database.crud import get_orders, get_user, assign_order_to_executor

# Этап для ввода ID заказа
CHOOSE_ORDER = 1

async def start_order_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    db = SessionLocal()
    user = get_user(db, user_id)

    if not user or user.user_type != "Исполнитель":
        await update.message.reply_text("❌ Только исполнители могут брать заказы в работу.")
        db.close()
        return ConversationHandler.END

    orders = get_orders(db)
    db.close()

    available_orders = [o for o in orders if o.status == "Ожидает выполнения"]
    if not available_orders:
        await update.message.reply_text("🔍 Нет доступных заказов.")
        return ConversationHandler.END

    response = "📜 Доступные заказы:\n\n"
    for order in available_orders:
        response += f"📌 {order.description}\n📎 ID: {order.id}\n\n"
    
    await update.message.reply_text(response + "Введите ID заказа, который хотите взять в работу:")

    return CHOOSE_ORDER

async def choose_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    order_id = update.message.text
    user_id = update.message.from_user.id

    if not order_id.isdigit():
        await update.message.reply_text("❌ Введите корректный ID заказа.")
        return CHOOSE_ORDER

    db = SessionLocal()
    order = assign_order_to_executor(db, int(order_id), user_id)
    db.close()

    if not order:
        await update.message.reply_text("❌ Этот заказ уже взят или не существует.")
        return CHOOSE_ORDER  # Остаемся в этом состоянии, ждем новый ввод

    await update.message.reply_text(f"✅ Вы взяли заказ ID {order_id} в работу. Удачи!")
    
    return ConversationHandler.END  # Завершаем диалог

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Выбор заказа отменен.")
    return ConversationHandler.END

def register(application):
    application.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔍 Посмотреть доступные заказы$"), start_order_assignment)],
        states={CHOOSE_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_order)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    ))
