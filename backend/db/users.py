from sqlalchemy import Column, Integer, Text, DateTime, func
from db.database import Base, SessionLocal
from logs.log_store import get_logger

logger = get_logger(__name__)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    password = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())


def get_user_by_id(id: str):
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == id).first()
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None
    finally:
        db.close()

def get_user(email: str):
    db = SessionLocal()
    try:
        return db.query(User).filter(User.email == email).first()
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None
    finally:
        db.close()


def add_user(name: str, email: str, password: str):
    db = SessionLocal()
    try:
        user = User(name=name, email=email, password=password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding user: {e}")
        return None
    finally:
        db.close()


def update_user_password(user_id: int, new_password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.password = new_password
            db.commit()
            return True
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating password: {e}")
        return None
    finally:
        db.close()
