"""
Product-related SQLAlchemy ORM models for spoXpro backend.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class ProductType(Base):
    """Product type model (e.g., T-Shirt, Shorts, Shoes)."""
    __tablename__ = "product_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    
    # Relationships
    products = relationship("Product", back_populates="product_type")
    
    def __repr__(self):
        return f"<ProductType(id={self.id}, name='{self.name}')>"


class Category(Base):
    """Category model (e.g., Men's Clothing, Women's Clothing)."""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    
    # Relationships
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class SportType(Base):
    """Sport type model (e.g., Football, Basketball, Running)."""
    __tablename__ = "sport_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    
    # Relationships
    products = relationship("Product", back_populates="sport_type")
    
    def __repr__(self):
        return f"<SportType(id={self.id}, name='{self.name}')>"


class Material(Base):
    """Material model (e.g., Cotton, Polyester, Mesh)."""
    __tablename__ = "materials"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    
    # Relationships
    products = relationship("Product", back_populates="material")
    
    def __repr__(self):
        return f"<Material(id={self.id}, name='{self.name}')>"


class Product(Base):
    """Main product model for sports clothing items."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # Foreign key relationships
    product_type_id = Column(Integer, ForeignKey("product_types.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    sport_type_id = Column(Integer, ForeignKey("sport_types.id"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, index=True)
    
    # Product attributes
    color = Column(String(50), nullable=False, index=True)
    gender = Column(String(10), nullable=False, index=True)  # male/female/unisex
    brand = Column(String(100), nullable=False, default="spoXpro", index=True)
    price = Column(Numeric(10, 2), nullable=False, index=True)
    
    # JSON fields
    reviews = Column(JSON, nullable=True, default=list)
    images = Column(JSON, nullable=False, default=list)  # List of image URLs
    
    # Unique identifiers
    article_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Metadata
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    product_views = Column(Integer, default=0, nullable=False, index=True)
    
    # Relationships
    product_type = relationship("ProductType", back_populates="products")
    category = relationship("Category", back_populates="products")
    sport_type = relationship("SportType", back_populates="products")
    material = relationship("Material", back_populates="products")
    sizes = relationship("ProductSize", back_populates="product", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', article_number='{self.article_number}')>"


class ProductSize(Base):
    """Product size model with inventory tracking."""
    __tablename__ = "product_sizes"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    size = Column(String(10), nullable=False, index=True)  # XXS, XS, S, M, L, XL, XXL, XXXL, XXXXL
    quantity = Column(Integer, nullable=False, default=0, index=True)
    
    # Relationships
    product = relationship("Product", back_populates="sizes")
    
    # Ensure unique size per product
    __table_args__ = (
        UniqueConstraint('product_id', 'size', name='unique_product_size'),
    )
    
    def __repr__(self):
        return f"<ProductSize(id={self.id}, product_id={self.product_id}, size='{self.size}', quantity={self.quantity})>"