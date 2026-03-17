from sqlalchemy import Column, Integer, Text, DateTime, CheckConstraint, ForeignKey, func
from db.database import Base, SessionLocal
from logs.log_store import get_logger

logger = get_logger(__name__)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    first_name = Column(Text, nullable=False)
    last_name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    phone = Column(Text, nullable=False)
    address = Column(Text, nullable=False)
    payment_status = Column(Text, default="pending")
    total_amount = Column(Integer, nullable=False)
    products_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        CheckConstraint("payment_status IN ('pending', 'paid', 'failed')"),
    )


def get_orders_by_user(user_id: int):
    db = SessionLocal()
    try:
        return db.query(Order).filter(Order.user_id == user_id).all()
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        return None
    finally:
        db.close()


def add_order(user_id: int, first_name: str, last_name: str, email: str,
              phone: str, address: str, total_amount: int, products_json: str = "[]",
              payment_status: str = "pending"):
    """
    json.dumps -> products_json -> json.loads
    """
    db = SessionLocal()
    try:
        order = Order(
            user_id=user_id, first_name=first_name, last_name=last_name,
            email=email, phone=phone, address=address,
            payment_status=payment_status, total_amount=total_amount,
            products_json=products_json
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding order: {e}")
        return None
    finally:
        db.close()
