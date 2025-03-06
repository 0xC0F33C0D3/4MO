from sqlalchemy import Column, Integer, String, ForeignKey  # Добавьте ForeignKey
from sqlalchemy.orm import relationship  # Также импортируйте relationship
from .database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    user_type = Column(String)  # Например, 'customer' или 'executor'
    
    # Добавьте здесь определение отношений
    orders = relationship("Order", back_populates="customer")

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    customer_id = Column(Integer, ForeignKey('users.id'))  # Теперь ForeignKey определен

    customer = relationship("User", back_populates="orders")