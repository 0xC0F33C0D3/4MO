from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from database.database import SessionLocal
from database.crud import get_user, update_executor_status

async def toggle_executor_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Меняет статус исполнителя (вышел на линию/ушел с линии)."""
    user_id = update.message.from_user.id
    db = SessionLocal()
    user = get_user(db, user_id)

    if not user or user.user_type != "Исполнитель":
        await update.message.reply_text("❌ Эта команда доступна только исполнителям.")
        db.close()
        return

    new_status = not user.is_online
    update_executor_status(db, user.id, new_status)
    db.close()

    status_text = "🟢 Вы вышли на линию! Теперь заказчики могут выбрать вас." if new_status else "🔴 Вы ушли с линии."
    await update.message.reply_text(status_text)

def register(application):
    application.add_handler(MessageHandler(filters.Regex("^✅ Выйти на линию$"), toggle_executor_status))
