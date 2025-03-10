from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler
from database.database import SessionLocal
from database.crud import get_user, get_finished_orders, get_order_by_id, update_order_status, create_order
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния диалога
CHOOSE_ORDER = 1

async def show_order_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает историю завершенных/отмененных заказов."""
    user_id = update.message.from_user.id
    db = SessionLocal()
    user = get_user(db, user_id)

    if not user:
        await update.message.reply_text("❌ Вы не зарегистрированы.")
        db.close()
        return ConversationHandler.END

    orders = get_finished_orders(db, user.id, user.user_type)
    db.close()

    if not orders:
        await update.message.reply_text("📜 У вас нет завершенных или отмененных заказов.")
        return ConversationHandler.END

    response = "📜 Ваши завершенные заказы:\n\n"
    for order in orders:
        response += f"📌 {order.description}\n📎 ID: {order.id} | Статус: {order.status}\n\n"

    await update.message.reply_text(response + "Введите ID заказа, чтобы выбрать его.")

    return CHOOSE_ORDER  # Ожидаем, пока пользователь выберет заказ

async def select_order_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Пользователь выбирает действие с завершенным заказом."""
    order_id = update.message.text

    if not order_id.isdigit():
        await update.message.reply_text("❌ Введите корректный ID заказа.")
        return CHOOSE_ORDER

    db = SessionLocal()
    order = get_order_by_id(db, int(order_id))
    db.close()

    if not order:
        await update.message.reply_text("❌ Заказ не найден.")
        return CHOOSE_ORDER

    context.user_data["selected_order_id"] = order.id

    keyboard = [
        ["🔄 Повторить заказ"],
        ["⭐ Изменить оценку"],
        ["📞 Связаться с пользователем"],
        ["🗑 Удалить заказ"],
        ["🔙 Назад"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(f"📦 Вы выбрали заказ ID {order.id}. Выберите действие:", reply_markup=reply_markup)
    
    return ConversationHandler.END  # Завершаем диалог

async def repeat_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создает копию завершенного заказа."""
    order_id = context.user_data.get("selected_order_id")
    if not order_id:
        await update.message.reply_text("❌ Ошибка: задание не выбрано.")
        return

    db = SessionLocal()
    order = get_order_by_id(db, order_id)

    if not order:
        await update.message.reply_text("❌ Ошибка: заказ не найден.")
        db.close()
        return

    new_order = create_order(db, order.description, order.customer_id)
    db.close()

    await update.message.reply_text(f"✅ Новый заказ создан на основе заказа ID {order_id}! (ID нового заказа: {new_order.id})")

async def delete_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Меняет статус заказа на 'Удалено'."""
    order_id = context.user_data.get("selected_order_id")
    if not order_id:
        await update.message.reply_text("❌ Ошибка: задание не выбрано.")
        return

    db = SessionLocal()
    order = get_order_by_id(db, order_id)

    if not order:
        await update.message.reply_text("❌ Ошибка: заказ не найден.")
        db.close()
        return

    await update_order_status(db, order_id, "Удалено")
    db.close()

    await update.message.reply_text(f"🗑 Заказ ID {order_id} удален.")

async def contact_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет контактные данные исполнителя или заказчика."""
    user_id = update.message.from_user.id
    db = SessionLocal()
    user = get_user(db, user_id)

    if not user:
        await update.message.reply_text("❌ Вы не зарегистрированы.")
        db.close()
        return

    order_id = context.user_data.get("selected_order_id")
    if not order_id:
        await update.message.reply_text("❌ Ошибка: задание не выбрано.")
        return

    order = get_order_by_id(db, order_id)
    db.close()

    if not order:
        await update.message.reply_text("❌ Ошибка: заказ не найден.")
        return

    contact_id = order.customer_id if user.user_type == "Исполнитель" else order.executor_id
    contact = get_user(db, contact_id)

    if contact and contact.username:
        await update.message.reply_text(f"📞 Связаться с @{contact.username}")
    else:
        await update.message.reply_text("❌ Ошибка: контакты пользователя недоступны.")

def register(application):
    application.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📜 История заказов$"), show_order_history)],
        states={CHOOSE_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_order_action)]},
        fallbacks=[]
    ))
    application.add_handler(MessageHandler(filters.Regex("^🔄 Повторить заказ$"), repeat_order))
    application.add_handler(MessageHandler(filters.Regex("^🗑 Удалить заказ$"), delete_order))
    application.add_handler(MessageHandler(filters.Regex("^📞 Связаться с пользователем$"), contact_user))
