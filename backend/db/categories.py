from sqlalchemy import Column, Integer, Text
from db.database import Base, SessionLocal
from logs.log_store import get_logger

logger = get_logger(__name__)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    tags = Column(Text, nullable=False)


def get_all_categories():
    db = SessionLocal()
    try:
        return db.query(Category).all()
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return None
    finally:
        db.close()


def add_category(name: str, tags: str):
    db = SessionLocal()
    try:
        category = Category(name=name, tags=tags)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding category: {e}")
        return None
    finally:
        db.close()


def delete_category(category_id: int):
    db = SessionLocal()
    try:
        category = db.query(Category).filter(Category.id == category_id).first()
        if category:
            db.delete(category)
            db.commit()
            return True
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting category: {e}")
        return None
    finally:
        db.close()
