from sqlalchemy.orm import Session
from .models import User, Order

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, username: str, user_type: str):
    db_user = User(username=username, user_type=user_type)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_order(db: Session, description: str, customer_id: int):
    db_order = Order(description=description, customer_id=customer_id)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def get_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Order).offset(skip).limit(limit).all()