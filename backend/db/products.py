from sqlalchemy import Column, Integer, Text, DateTime, CheckConstraint, ForeignKey, func
from sqlalchemy.orm import relationship, joinedload
from sqlalchemy_file import ImageField
from db.database import Base, SessionLocal
from logs.log_store import get_logger

logger = get_logger(__name__)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    price = Column(Integer, nullable=False)
    gender = Column(Text)
    discount = Column(Integer, default=0)
    color = Column(Text)
    type = Column(Text)
    sizes = Column(Text, nullable=False, default="[]")
    images = Column(ImageField(multiple=True))
    stock_quantity = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", backref="products")
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        CheckConstraint("gender IN ('M', 'F', 'U')"),
        CheckConstraint("stock_quantity >= 0"),
    )


def get_all_products():
    db = SessionLocal()
    try:
        return db.query(Product).options(joinedload(Product.category)).all()
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return None
    finally:
        db.close()

def get_products_by_list_id(product_ids: list[int]) -> list[Product]:
    db = SessionLocal()
    try:
        return (
            db.query(Product)
            .options(joinedload(Product.category))
            .filter(Product.id.in_(product_ids))
            .all()
        )
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return None
    finally:
        db.close()

def get_product(product_id: int) -> Product:
    db = SessionLocal()
    try:
        return db.query(Product).options(joinedload(Product.category)).filter(Product.id == product_id).first()
    except Exception as e:
        logger.error(f"Error getting product: {e}")
        return None
    finally:
        db.close()


def add_product(name: str, price: int, sizes: str = "[]", images: str = "[]",
                description: str = None, gender: str = None, discount: int = None,
                color: str = None, type_: str = None, stock_quantity: int = 0,
                category_id: int = None):
    db = SessionLocal()
    try:
        product = Product(
            name=name, description=description, price=price,
            gender=gender, discount=discount, color=color,
            type=type_, sizes=sizes, images=images,
            stock_quantity=stock_quantity, category_id=category_id
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding product: {e}")
        return None
    finally:
        db.close()


def update_product(product_id: int, **kwargs):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        db.commit()
        db.refresh(product)
        return product
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating product: {e}")
        return None
    finally:
        db.close()


def delete_product(product_id: int):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            db.delete(product)
            db.commit()
            return True
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting product: {e}")
        return None
    finally:
        db.close()


from pathlib import Path
from config.settings import get_settings
import json

def images_list_path(images: list):
    path_image_folder = get_settings().images_url_prefix
    list_images = []
    for i in images:
        path_image = '\img' + str(Path(path_image_folder, i["file_id"]))
        list_images.append(path_image)
    return list_images

def to_dict_product(i: Product, one_image: bool = False):
    return {
        "id": i.id,
        "name": i.name,
        "image": images_list_path(i.images)[0] if one_image else images_list_path(i.images),
        "discountPercent": i.discount,
        "description": i.description,
        "price": i.price,
        "size": json.loads(i.sizes)[0] if one_image else json.loads(i.sizes),
        "color": i.color,
        "categoryId": i.category_id,
        "type": "accessories" if i.category.tags == "accessories" else "clothing"
    }

def to_dict_product_full(result: Product):
    return {
            "id": result.id,
            "name": result.name,
            "description": result.description,
            "price": result.price,
            "discountPercent": result.discount,
            "stockQuantity": result.stock_quantity,
            "size": json.loads(result.sizes),
            "color": result.color,
            "gender": result.gender,
            "images": images_list_path(result.images),
            "category": {
                "name": result.category.name,
                "categoryId": result.category_id,
            }
    }