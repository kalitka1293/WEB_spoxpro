"""
Order and cart-related SQLAlchemy ORM models for spoXpro backend.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base


class CartItem(Base):
    """Cart item model supporting both authenticated users and guest cookies."""
    __tablename__ = "cart_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Null for guest users
    cookie = Column(String(255), nullable=True, index=True)  # For guest users
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    size = Column(String(10), nullable=False)  # XXS, XS, S, M, L, XL, XXL, XXXL, XXXXL
    quantity = Column(Integer, nullable=False, default=1)
    added_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")
    
    def __repr__(self):
        return f"<CartItem(id={self.id}, user_id={self.user_id}, cookie='{self.cookie}', product_id={self.product_id}, size='{self.size}', quantity={self.quantity})>"


class Order(Base):
    """Order model for completed purchases."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, confirmed, shipped, delivered, cancelled
    created_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, total_amount={self.total_amount}, status='{self.status}')>"


class OrderItem(Base):
    """Order item model for individual products within an order."""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    size = Column(String(10), nullable=False)  # XXS, XS, S, M, L, XL, XXL, XXXL, XXXXL
    quantity = Column(Integer, nullable=False)
    price_at_time = Column(Numeric(10, 2), nullable=False)  # Price when order was placed
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id}, size='{self.size}', quantity={self.quantity}, price_at_time={self.price_at_time})>"