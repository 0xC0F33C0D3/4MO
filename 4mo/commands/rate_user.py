from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters, ConversationHandler
from database.database import SessionLocal
from database.crud import get_user, get_order_by_id, update_user_rating
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для диалога
CHOOSE_RATING = 1

async def request_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Запрашивает оценку у пользователя после завершения заказа."""
    order_id = context.user_data.get("selected_order_id")
    if not order_id:
        await update.message.reply_text("❌ Ошибка: заказ не найден.")
        return ConversationHandler.END

    user_id = update.message.from_user.id
    db = SessionLocal()
    order = get_order_by_id(db, order_id)
    user = get_user(db, user_id)
    db.close()

    if not order or not user:
        await update.message.reply_text("❌ Ошибка: заказ или пользователь не найдены.")
        return ConversationHandler.END

    # Определяем, кого оценивает пользователь
    if user.id == order.customer_id:
        if order.executor_id is None:
            await update.message.reply_text("❌ У этого заказа нет исполнителя, оценка невозможна.")
            return ConversationHandler.END
        context.user_data["rated_user_id"] = order.executor_id
        role = "исполнителя"
    else:
        context.user_data["rated_user_id"] = order.customer_id
        role = "заказчика"

    logger.info(f"Запрос оценки: {user.username} оценивает {role} (ID {context.user_data['rated_user_id']})")

    keyboard = [["1", "2", "3", "4", "5"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(f"⭐ Пожалуйста, оцените {role} по шкале от 1 до 5:", reply_markup=reply_markup)
    
    return CHOOSE_RATING

async def receive_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Сохраняет оценку в базе данных."""
    rating = update.message.text
    if rating not in ["1", "2", "3", "4", "5"]:
        await update.message.reply_text("❌ Введите число от 1 до 5.")
        return CHOOSE_RATING

    rated_user_id = context.user_data.get("rated_user_id")
    if not rated_user_id:
        await update.message.reply_text("❌ Ошибка: пользователь для оценки не найден.")
        logger.error("Ошибка: rated_user_id не найден в context.user_data")
        return ConversationHandler.END

    db = SessionLocal()
    rated_user = get_user(db, rated_user_id)  # Получаем пользователя, которого оценивают

    if not rated_user:
        await update.message.reply_text("❌ Ошибка: пользователь для оценки не найден в базе данных.")
        logger.error(f"Ошибка: Пользователь с ID {rated_user_id} не найден в базе.")
        db.close()
        return ConversationHandler.END

    update_user_rating(db, rated_user.id, int(rating))  # ✅ Исправлено: передаем rated_user.id
    db.close()

    logger.info(f"✅ Оценка сохранена: пользователь ID {rated_user_id} получил {rating} ⭐")

    await update.message.reply_text(f"✅ Спасибо! Ваша оценка {rating} сохранена.")
    
    return ConversationHandler.END


def register(application):
    application.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^⭐ Оценить пользователя$"), request_rating)],
        states={CHOOSE_RATING: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_rating)]},
        fallbacks=[],
        allow_reentry=True  # Позволяет повторно начинать диалог
    ))
