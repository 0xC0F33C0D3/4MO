from sqlalchemy.orm import Session
from .models import User, Order
from datetime import datetime

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
        status="Ожидает выполнения"
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def get_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Order).offset(skip).limit(limit).all()

def get_active_orders_for_executor(db: Session, executor_id: int):
    return db.query(Order).filter(Order.executor_id == executor_id, Order.status == "В работе").all()

def get_unfinished_orders_for_customer(db: Session, customer_id: int):
    return db.query(Order).filter(Order.customer_id == customer_id, Order.status != "Завершен").all()

def assign_order_to_executor(db: Session, order_id: int, executor_id: int):
    order = db.query(Order).filter(Order.id == order_id, Order.status == "Ожидает выполнения").first()
    if not order:
        return None  # Заказ уже взят или не существует
    
    order.executor_id = executor_id
    order.status = "В работе"
    db.commit()
    db.refresh(order)
    return order

