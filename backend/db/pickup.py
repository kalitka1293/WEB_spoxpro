from sqlalchemy import Column, Integer, Text
from db.database import Base, SessionLocal
from logs.log_store import get_logger

logger = get_logger(__name__)


class Pickup(Base):
    __tablename__ = "pickup"

    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(Text, nullable=False)


def get_all_pickups():
    db = SessionLocal()
    try:
        return db.query(Pickup).all()
    except Exception as e:
        logger.error(f"Error getting pickups: {e}")
        return None
    finally:
        db.close()


def add_pickup(address: str):
    db = SessionLocal()
    try:
        item = Pickup(address=address)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding pickup: {e}")
        return None
    finally:
        db.close()


def update_pickup(pickup_id: int, address: str):
    db = SessionLocal()
    try:
        item = db.query(Pickup).filter(Pickup.id == pickup_id).first()
        if item:
            item.address = address
            db.commit()
            return item
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating pickup: {e}")
        return None
    finally:
        db.close()


def delete_pickup(pickup_id: int):
    db = SessionLocal()
    try:
        item = db.query(Pickup).filter(Pickup.id == pickup_id).first()
        if item:
            db.delete(item)
            db.commit()
            return True
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting pickup: {e}")
        return None
    finally:
        db.close()
