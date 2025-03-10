from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database.models import Order
from database.database import SessionLocal
from database.crud import get_user, update_order_status, get_order_by_id
from commands.rate_user import request_rating

async def start_order_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Пользователь выбирает заказ для управления"""
    user_id = update.message.from_user.id
    db = SessionLocal()
    user = get_user(db, user_id)

    if not user:
        await update.message.reply_text("❌ Вы не зарегистрированы.")
        db.close()
        return ConversationHandler.END

    # Получаем активные или незавершенные заказы
    if user.user_type == "Исполнитель":
        orders = db.query(Order).filter(Order.executor_id == user.id, Order.status == "В работе").all()
    else:
        orders = db.query(Order).filter(Order.customer_id == user.id, Order.status != "Завершенный").all()
    
    db.close()

    if not orders:
        await update.message.reply_text("📂 У вас нет доступных заказов для управления.")
        return ConversationHandler.END

    response = "📋 Выберите ID заказа для управления:\n\n"
    for order in orders:
        response += f"📌 {order.description}\n📎 ID: {order.id} | Статус: {order.status}\n\n"

    await update.message.reply_text(response + "Введите ID заказа:")

    return CHOOSE_ORDER  # Переход к следующему этапу
# Функция для создания клавиатуры управления заказом
def get_order_management_keyboard(user_type):
    if user_type == "Исполнитель":
        keyboard = [
            ["✅ Подтвердить выполнение"],
            ["📞 Связаться с заказчиком"],
            ["❌ Отменить заказ"]
        ]
    else:
        keyboard = [
            ["✅ Подтвердить выполнение"],
            ["📞 Связаться с исполнителем"],
            ["❌ Отменить заказ"]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Функция подтверждения выполнения заказа
async def confirm_completion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    order_id = context.user_data.get("selected_order_id")
    print(order_id)
    user_id = update.message.from_user.id

    if not order_id:
        await update.message.reply_text("❌ Ошибка: задание не выбрано.")
        return ConversationHandler.END

    db = SessionLocal()
    user = get_user(db, user_id)
    order = get_order_by_id(db, order_id)

    if not order or (user.user_type == "Исполнитель" and order.executor_id != user.id) or (user.user_type == "Заказчик" and order.customer_id != user.id):
        await update.message.reply_text("❌ У вас нет доступа к этому заказу.")
        db.close()
        return ConversationHandler.END

    if order.status == "В работе":
        await update_order_status(db, order.id, "Завершенный")
        await update.message.reply_text(f"✅ Заказ ID {order_id} завершен!")
        
        db.close()
        
        # ✅ Запускаем диалог оценки корректно
        return await request_rating(update, context)  
    else:
        await update.message.reply_text("❌ Ошибка: заказ не найден.")
    
    db.close()
    return ConversationHandler.END


# Функция отмены заказа
async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    if not order or (user.user_type == "Исполнитель" and order.executor_id != user.id) or (user.user_type == "Заказчик" and order.customer_id != user.id):
        await update.message.reply_text("❌ У вас нет доступа к этому заказу.")
        db.close()
        return

    if user.user_type == "Исполнитель":
        if order.status == "В работе":
            new_status = "Новый"  # Освобождаем заказ для других исполнителей
            order.executor_id = None  # Убираем исполнителя
            await update.message.reply_text("❌ Вы убранны с заказа.")
        else:
            await update.message.reply_text("Заказ уже отменен или завершен")
            db.close()
            return
    else:  # Заказчик
        if order.customer_id != user.telegram_id:
            await update.message.reply_text("❌ Вы не можете отменить этот заказ.")
            db.close()
            return
        new_status = "Отменен"  # Заказ полностью отменен

    await update_order_status(db, order_id, new_status)
    db.close()

    await update.message.reply_text(f"🚫 Заказ ID {order_id} теперь имеет статус: {new_status}")

# Функция связи между заказчиком и исполнителем
async def contact_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    if not order or (user.user_type == "Исполнитель" and order.executor_id != user.id) or (user.user_type == "Заказчик" and order.customer_id != user.id):
        await update.message.reply_text("❌ У вас нет доступа к этому заказу.")
        db.close()
        return

    contact_id = order.customer_id if user.user_type == "Исполнитель" else order.executor_id
    contact = get_user(db, contact_id)
    db.close()

    if contact and contact.username:
        await update.message.reply_text(f"📞 Связаться с @{contact.username}")
    else:
        await update.message.reply_text("❌ Ошибка: контакты пользователя недоступны.")

CHOOSE_ORDER = 1



async def receive_order_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняем ID заказа и переходим в меню управления"""
    user_id = update.message.from_user.id
    db = SessionLocal()
    user = get_user(db, user_id)
    db.close()
    order_id = update.message.text

    if not order_id.isdigit():
        await update.message.reply_text("❌ Введите корректный ID заказа.")
        return CHOOSE_ORDER

    context.user_data["selected_order_id"] = int(order_id)
    reply_markup = get_order_management_keyboard(user.user_type)
    await update.message.reply_text(f"✅ Заказ ID {order_id} выбран. Теперь выберите действие в меню.", reply_markup=reply_markup)

    return ConversationHandler.END  # Завершаем диалог


# Регистрация команд
def register(application):
    application.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📦 Управление заказом$"), start_order_selection)],
        states={CHOOSE_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_order_id)]},
        fallbacks=[]
    ))
    application.add_handler(MessageHandler(filters.Regex("^✅ Подтвердить выполнение$"), confirm_completion))
    application.add_handler(MessageHandler(filters.Regex("^❌ Отменить заказ$"), cancel_order))
    application.add_handler(MessageHandler(filters.Regex("^📞 Связаться с .*"), contact_user))
