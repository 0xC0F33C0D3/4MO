from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    user_type = Column(String)  # 'customer' или 'executor'
    balance = Column(Float, default=0.0)
    rating = Column(Float, default=0.0)
    registered_at = Column(DateTime, default=datetime.utcnow)  # Дата регистрации

    # Связь с заказами, которые пользователь создал
    orders = relationship("Order", foreign_keys="[Order.customer_id]", back_populates="customer")

    # Связь с заказами, которые пользователь выполняет
    assigned_orders = relationship("Order", foreign_keys="[Order.executor_id]", back_populates="executor")

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)  # Дата создания заказа
    status = Column(String, default="Ожидает выполнения")  # Статус заказа
    customer_id = Column(Integer, ForeignKey('users.id'))
    executor_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Кто взял заказ

    customer = relationship("User", foreign_keys=[customer_id], back_populates="orders")
    executor = relationship("User", foreign_keys=[executor_id], back_populates="assigned_orders")
