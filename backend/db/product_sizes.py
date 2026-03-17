from sqlalchemy import Column, Integer, Text
from db.database import Base, SessionLocal
from logs.log_store import get_logger

logger = get_logger(__name__)


class ProductSize(Base):
    __tablename__ = "product_sizes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)


def get_all_sizes():
    db = SessionLocal()
    try:
        return db.query(ProductSize).all()
    except Exception as e:
        logger.error(f"Error getting sizes: {e}")
        return None
    finally:
        db.close()


def add_size(name: str):
    db = SessionLocal()
    try:
        size = ProductSize(name=name)
        db.add(size)
        db.commit()
        db.refresh(size)
        return size
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding size: {e}")
        return None
    finally:
        db.close()


def delete_size(size_id: int):
    db = SessionLocal()
    try:
        size = db.query(ProductSize).filter(ProductSize.id == size_id).first()
        if size:
            db.delete(size)
            db.commit()
            return True
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting size: {e}")
        return None
    finally:
        db.close()
