from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, CheckConstraint, func
from db.database import Base, SessionLocal
from logs.log_store import get_logger

logger = get_logger(__name__)


class Basket(Base):
    __tablename__ = "basket"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    size = Column(Text, nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        CheckConstraint("quantity > 0"),
    )


def get_basket_by_user(user_id: int):
    db = SessionLocal()
    try:
        return db.query(Basket).filter(Basket.user_id == user_id).all()
    except Exception as e:
        logger.error(f"Error getting basket: {e}")
        return None
    finally:
        db.close()


def add_to_basket(product_id: int, user_id: int, size: str, quantity: int):
    db = SessionLocal()
    try:
        item = Basket(product_id=product_id, user_id=user_id, size=size, quantity=quantity)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding to basket: {e}")
        return None
    finally:
        db.close()


def delete_basket_item(product_id: int, user_id):
    db = SessionLocal()
    try:
        item = db.query(Basket).filter(
            Basket.product_id == product_id,
            Basket.user_id == user_id
        ).first()
        if item:
            db.delete(item)
            db.commit()
            return True
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting basket item: {e}")
        return None
    finally:
        db.close()
