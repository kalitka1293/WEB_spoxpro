from sqlalchemy import Column, Integer, Text, DateTime, CheckConstraint, ForeignKey, func
from db.database import Base, SessionLocal
from logs.log_store import get_logger

logger = get_logger(__name__)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id"))
    username = Column(Text, nullable=False)
    rating = Column(Integer)
    text = Column(Text)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5"),
    )


def get_reviews_by_product(product_id: int):
    db = SessionLocal()
    try:
        return db.query(Review).filter(Review.product_id == product_id).all()
    except Exception as e:
        logger.error(f"Error getting reviews: {e}")
        return None
    finally:
        db.close()


def add_review(product_id: int, username: str, rating: int = None,
               text: str = None, user_id: int = None):
    db = SessionLocal()
    try:
        review = Review(
            product_id=product_id, user_id=user_id,
            username=username, rating=rating, text=text
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding review: {e}")
        return None
    finally:
        db.close()


def delete_review(review_id: int):
    db = SessionLocal()
    try:
        review = db.query(Review).filter(Review.id == review_id).first()
        if review:
            db.delete(review)
            db.commit()
            return True
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting review: {e}")
        return None
    finally:
        db.close()
