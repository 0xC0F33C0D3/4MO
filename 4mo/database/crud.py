from sqlalchemy.orm import Session
from .models import User, Order
from datetime import datetime
import os
from dotenv import load_dotenv
from telegram import Bot


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.telegram_id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, telegram_id: int, username: str, user_type: str):
    existing_user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if existing_user:
        return existing_user  # Если пользователь уже есть, возвращаем его
    
    db_user = User(
        telegram_id=telegram_id,
        username=username,
        user_type=user_type,
        balance=0.0,
        rating=0.0,
        registered_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_order(db: Session, description: str, customer_id: int):
    db_order = Order(
        description=description,
        customer_id=customer_id,
        created_at=datetime.utcnow(),
        status="Новый"
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def get_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Order).filter(Order.status == "Новый").all()

def get_order_by_id(db: Session, order_id: int):
    return db.query(Order).filter(Order.id == order_id).first()


def get_active_orders_for_executor(db: Session, executor_id: int):
    return db.query(Order).filter(Order.executor_id == executor_id, Order.status == "В работе").all()

def get_unfinished_orders_for_customer(db: Session, customer_id: int):
    return db.query(Order).filter(Order.customer_id == customer_id, Order.status != "Завершен").all()

def get_finished_orders(db: Session, user_id: int, user_type: str):
    """Возвращает завершенные или отмененные заказы пользователя."""
    if user_type == "Заказчик":
        return db.query(Order).filter(Order.customer_id == user_id, Order.status.in_(["Завершенный", "Отменен"])).all()
    else:
        return db.query(Order).filter(Order.executor_id == user_id, Order.status.in_(["Завершенный", "Отменен"])).all()
    
def get_active_executors(db: Session):
    """Возвращает список активных исполнителей."""
    return db.query(User).filter(User.user_type == "Исполнитель", User.is_online == True).all()



async def assign_order_to_executor(db: Session, order_id: int, executor_id: int):
    order = db.query(Order).filter(Order.id == order_id, Order.status == "Новый").first()
    if not order:
        return None  # Заказ уже взят или не существует
    
    order.executor_id = executor_id
    await update_order_status(db, order_id, "В работе")
    db.commit()
    db.refresh(order)
    return order

def update_executor_status(db: Session, user_id: int, is_online: bool):
    """Обновляет статус исполнителя (на линии или нет)."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_online = is_online
        db.commit()


async def update_order_status(db: Session, order_id: int, new_status: str):
    """Обновляет статус заказа и уведомляет заказчика и исполнителя"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return None  # Если заказ не найден

    old_status = order.status  # Запоминаем предыдущий статус
    order.status = new_status
    db.commit()
    db.refresh(order)

    message_text = f"🔔 Статус вашего заказа ID {order_id} изменился: {old_status} => {new_status}"

    # Уведомляем заказчика
    customer = db.query(User).filter(User.id == order.customer_id).first()
    if customer:
        try:
            await bot.send_message(chat_id=customer.telegram_id, text=message_text)
        except Exception as e:
            print(f"Ошибка отправки уведомления заказчику: {e}")

    # Уведомляем исполнителя (если заказ взят)
    if order.executor_id:
        executor = db.query(User).filter(User.id == order.executor_id).first()
        if executor:
            try:
                await bot.send_message(chat_id=executor.telegram_id, text=message_text)
            except Exception as e:
                print(f"Ошибка отправки уведомления исполнителю: {e}")

    return order

def update_user_rating(db: Session, user_id: int, new_rating: int):
    """Обновляет средний рейтинг пользователя."""
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        return

    total_score = user.rating * user.rating_count  # Текущая сумма оценок
    user.rating_count += 1  # Увеличиваем количество оценок
    user.rating = (total_score + new_rating) / user.rating_count  # Вычисляем средний рейтинг

    db.commit()
    db.refresh(user)
