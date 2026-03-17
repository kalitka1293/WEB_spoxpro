from sqlalchemy import Column, Integer, Text
from db.database import Base, SessionLocal
from logs.log_store import get_logger

logger = get_logger(__name__)


class ProductColor(Base):
    __tablename__ = "product_colors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)


def get_all_colors():
    db = SessionLocal()
    try:
        return db.query(ProductColor).all()
    except Exception as e:
        logger.error(f"Error getting colors: {e}")
        return None
    finally:
        db.close()


def add_color(name: str):
    db = SessionLocal()
    try:
        color = ProductColor(name=name)
        db.add(color)
        db.commit()
        db.refresh(color)
        return color
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding color: {e}")
        return None
    finally:
        db.close()


def delete_color(color_id: int):
    db = SessionLocal()
    try:
        color = db.query(ProductColor).filter(ProductColor.id == color_id).first()
        if color:
            db.delete(color)
            db.commit()
            return True
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting color: {e}")
        return None
    finally:
        db.close()
