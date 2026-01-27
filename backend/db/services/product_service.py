"""
Product database service for spoXpro backend.

This service provides comprehensive CRUD operations for products and related tables,
including filtering, search, inventory management, and view count tracking.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db.models.product import (
    Product, ProductSize, ProductType, Category, SportType, Material
)
from logs.log_store import get_logger

logger = get_logger(__name__)


class ProductService:
    """Service class for product-related database operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the ProductService with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    # ==================== PRODUCT CRUD OPERATIONS ====================
    
    def create_product(self, product_data: Dict[str, Any]) -> Optional[Product]:
        """
        Create a new product with sizes.
        
        Args:
            product_data: Dictionary containing product information including:
                - name: str
                - description: str
                - product_type_id: int
                - category_id: int
                - sport_type_id: int
                - material_id: int
                - color: str
                - gender: str (male/female/unisex)
                - brand: str (optional, defaults to "spoXpro")
                - price: Decimal
                - reviews: List[dict] (optional)
                - article_number: str
                - images: List[str] (optional)
                - sizes: List[dict] with size and quantity
        
        Returns:
            Product: Created product instance or None if creation failed
        """
        try:
            # Extract sizes data before creating product
            sizes_data = product_data.pop('sizes', [])
            
            # Create product instance
            product = Product(**product_data)
            self.db.add(product)
            self.db.flush()  # Get the product ID
            
            # Add sizes if provided
            if sizes_data:
                for size_data in sizes_data:
                    product_size = ProductSize(
                        product_id=product.id,
                        size=size_data['size'],
                        quantity=size_data.get('quantity', 0)
                    )
                    self.db.add(product_size)
            
            self.db.commit()
            logger.info(f"Created product: {product.name} (ID: {product.id})")
            return product
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating product: {e}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating product: {e}", exc_info=True)
            return None
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Get a product by its ID with all related data.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product: Product instance or None if not found
        """
        try:
            product = (
                self.db.query(Product)
                .options(
                    joinedload(Product.product_type),
                    joinedload(Product.category),
                    joinedload(Product.sport_type),
                    joinedload(Product.material),
                    joinedload(Product.sizes)
                )
                .filter(Product.id == product_id)
                .first()
            )
            
            if product:
                logger.debug(f"Retrieved product: {product.name} (ID: {product_id})")
            else:
                logger.warning(f"Product not found: ID {product_id}")
                
            return product
            
        except Exception as e:
            logger.error(f"Error retrieving product {product_id}: {e}", exc_info=True)
            return None
    
    def get_product_by_article_number(self, article_number: str) -> Optional[Product]:
        """
        Get a product by its article number.
        
        Args:
            article_number: Product article number
            
        Returns:
            Product: Product instance or None if not found
        """
        try:
            product = (
                self.db.query(Product)
                .options(
                    joinedload(Product.product_type),
                    joinedload(Product.category),
                    joinedload(Product.sport_type),
                    joinedload(Product.material),
                    joinedload(Product.sizes)
                )
                .filter(Product.article_number == article_number)
                .first()
            )
            
            if product:
                logger.debug(f"Retrieved product by article number: {article_number}")
            else:
                logger.warning(f"Product not found: article number {article_number}")
                
            return product
            
        except Exception as e:
            logger.error(f"Error retrieving product by article number {article_number}: {e}", exc_info=True)
            return None
    
    def update_product(self, product_id: int, updates: Dict[str, Any]) -> Optional[Product]:
        """
        Update a product's information.
        
        Args:
            product_id: Product ID
            updates: Dictionary of fields to update
            
        Returns:
            Product: Updated product instance or None if update failed
        """
        try:
            product = self.get_product_by_id(product_id)
            if not product:
                return None
            
            # Handle sizes update separately
            sizes_data = updates.pop('sizes', None)
            
            # Update product fields
            for field, value in updates.items():
                if hasattr(product, field):
                    setattr(product, field, value)
            
            # Update sizes if provided
            if sizes_data is not None:
                # Remove existing sizes
                self.db.query(ProductSize).filter(ProductSize.product_id == product_id).delete()
                
                # Add new sizes
                for size_data in sizes_data:
                    product_size = ProductSize(
                        product_id=product_id,
                        size=size_data['size'],
                        quantity=size_data.get('quantity', 0)
                    )
                    self.db.add(product_size)
            
            self.db.commit()
            logger.info(f"Updated product: {product.name} (ID: {product_id})")
            return product
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error updating product {product_id}: {e}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating product {product_id}: {e}", exc_info=True)
            return None
    
    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product and all its related data.
        
        Args:
            product_id: Product ID
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            product = self.get_product_by_id(product_id)
            if not product:
                logger.warning(f"Cannot delete product: ID {product_id} not found")
                return False
            
            product_name = product.name
            self.db.delete(product)
            self.db.commit()
            
            logger.info(f"Deleted product: {product_name} (ID: {product_id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting product {product_id}: {e}", exc_info=True)
            return False
    
    # ==================== PRODUCT SEARCH AND FILTERING ====================
    
    def get_products_filtered(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_date",
        sort_order: str = "desc",
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Product]:
        """
        Get products with filtering, sorting, and pagination.
        
        Args:
            filters: Dictionary of filter criteria:
                - category: str or int (name or ID)
                - product_type: str or int (name or ID)
                - sport_type: str or int (name or ID)
                - material: str or int (name or ID)
                - color: str
                - gender: str (male/female/unisex)
                - brand: str
                - min_price: Decimal
                - max_price: Decimal
                - size: str (check size availability)
                - search: str (search in name and description)
            sort_by: Field to sort by (default: created_date)
            sort_order: Sort order "asc" or "desc" (default: desc)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Product]: List of matching products
        """
        try:
            query = (
                self.db.query(Product)
                .options(
                    joinedload(Product.product_type),
                    joinedload(Product.category),
                    joinedload(Product.sport_type),
                    joinedload(Product.material),
                    joinedload(Product.sizes)
                )
            )
            
            # Apply filters
            if filters:
                query = self._apply_product_filters(query, filters)
            
            # Apply sorting
            if hasattr(Product, sort_by):
                sort_column = getattr(Product, sort_by)
                if sort_order.lower() == "asc":
                    query = query.order_by(asc(sort_column))
                else:
                    query = query.order_by(desc(sort_column))
            
            # Apply pagination
            if offset > 0:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            products = query.all()
            logger.debug(f"Retrieved {len(products)} products with filters: {filters}")
            return products
            
        except Exception as e:
            logger.error(f"Error retrieving filtered products: {e}", exc_info=True)
            return []
    
    def _apply_product_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to a product query."""
        
        # Category filter
        if 'category' in filters and filters['category']:
            category_value = filters['category']
            if isinstance(category_value, int):
                query = query.filter(Product.category_id == category_value)
            else:
                query = query.join(Category).filter(Category.name.ilike(f"%{category_value}%"))
        
        # Product type filter
        if 'product_type' in filters and filters['product_type']:
            type_value = filters['product_type']
            if isinstance(type_value, int):
                query = query.filter(Product.product_type_id == type_value)
            else:
                query = query.join(ProductType).filter(ProductType.name.ilike(f"%{type_value}%"))
        
        # Sport type filter
        if 'sport_type' in filters and filters['sport_type']:
            sport_value = filters['sport_type']
            if isinstance(sport_value, int):
                query = query.filter(Product.sport_type_id == sport_value)
            else:
                query = query.join(SportType).filter(SportType.name.ilike(f"%{sport_value}%"))
        
        # Material filter
        if 'material' in filters and filters['material']:
            material_value = filters['material']
            if isinstance(material_value, int):
                query = query.filter(Product.material_id == material_value)
            else:
                query = query.join(Material).filter(Material.name.ilike(f"%{material_value}%"))
        
        # Color filter
        if 'color' in filters and filters['color']:
            query = query.filter(Product.color.ilike(f"%{filters['color']}%"))
        
        # Gender filter
        if 'gender' in filters and filters['gender']:
            query = query.filter(Product.gender == filters['gender'])
        
        # Brand filter
        if 'brand' in filters and filters['brand']:
            query = query.filter(Product.brand.ilike(f"%{filters['brand']}%"))
        
        # Price range filters
        if 'min_price' in filters and filters['min_price'] is not None:
            query = query.filter(Product.price >= filters['min_price'])
        
        if 'max_price' in filters and filters['max_price'] is not None:
            query = query.filter(Product.price <= filters['max_price'])
        
        # Size availability filter
        if 'size' in filters and filters['size']:
            query = query.join(ProductSize).filter(
                and_(
                    ProductSize.size == filters['size'],
                    ProductSize.quantity > 0
                )
            )
        
        # Search filter (name and description)
        if 'search' in filters and filters['search']:
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term)
                )
            )
        
        return query
    
    def search_products(self, search_term: str, limit: int = 50) -> List[Product]:
        """
        Search products by name, description, or article number.
        
        Args:
            search_term: Search term
            limit: Maximum number of results
            
        Returns:
            List[Product]: List of matching products
        """
        return self.get_products_filtered(
            filters={'search': search_term},
            limit=limit
        )
    
    # ==================== PRODUCT VIEW COUNT ====================
    
    def increment_product_views(self, product_id: int) -> bool:
        """
        Increment the view count for a product.
        
        Args:
            product_id: Product ID
            
        Returns:
            bool: True if increment successful, False otherwise
        """
        try:
            result = (
                self.db.query(Product)
                .filter(Product.id == product_id)
                .update({Product.product_views: Product.product_views + 1})
            )
            
            if result > 0:
                self.db.commit()
                logger.debug(f"Incremented view count for product ID: {product_id}")
                return True
            else:
                logger.warning(f"Product not found for view increment: ID {product_id}")
                return False
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error incrementing product views {product_id}: {e}", exc_info=True)
            return False
    
    # ==================== INVENTORY MANAGEMENT ====================
    
    def get_product_inventory(self, product_id: int, size: Optional[str] = None) -> Union[Dict[str, int], int, None]:
        """
        Get inventory information for a product.
        
        Args:
            product_id: Product ID
            size: Specific size (optional)
            
        Returns:
            Dict[str, int]: Size -> quantity mapping if no size specified
            int: Quantity for specific size
            None: If product not found
        """
        try:
            if size:
                # Get quantity for specific size
                product_size = (
                    self.db.query(ProductSize)
                    .filter(
                        and_(
                            ProductSize.product_id == product_id,
                            ProductSize.size == size
                        )
                    )
                    .first()
                )
                return product_size.quantity if product_size else 0
            else:
                # Get all sizes and quantities
                sizes = (
                    self.db.query(ProductSize)
                    .filter(ProductSize.product_id == product_id)
                    .all()
                )
                return {size.size: size.quantity for size in sizes}
                
        except Exception as e:
            logger.error(f"Error getting inventory for product {product_id}: {e}", exc_info=True)
            return None
    
    def update_product_inventory(self, product_id: int, size: str, quantity_change: int) -> bool:
        """
        Update inventory for a specific product size.
        
        Args:
            product_id: Product ID
            size: Product size
            quantity_change: Change in quantity (positive to add, negative to subtract)
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            product_size = (
                self.db.query(ProductSize)
                .filter(
                    and_(
                        ProductSize.product_id == product_id,
                        ProductSize.size == size
                    )
                )
                .first()
            )
            
            if not product_size:
                logger.warning(f"Product size not found: product {product_id}, size {size}")
                return False
            
            new_quantity = product_size.quantity + quantity_change
            
            # Prevent negative inventory
            if new_quantity < 0:
                logger.warning(f"Cannot reduce inventory below zero: product {product_id}, size {size}")
                return False
            
            product_size.quantity = new_quantity
            self.db.commit()
            
            logger.info(f"Updated inventory: product {product_id}, size {size}, change {quantity_change}, new quantity {new_quantity}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating inventory: product {product_id}, size {size}: {e}", exc_info=True)
            return False
    
    def check_inventory_availability(self, product_id: int, size: str, required_quantity: int) -> bool:
        """
        Check if sufficient inventory is available for a product size.
        
        Args:
            product_id: Product ID
            size: Product size
            required_quantity: Required quantity
            
        Returns:
            bool: True if sufficient inventory available, False otherwise
        """
        try:
            current_quantity = self.get_product_inventory(product_id, size)
            if current_quantity is None:
                return False
            
            available = current_quantity >= required_quantity
            logger.debug(f"Inventory check: product {product_id}, size {size}, required {required_quantity}, available {current_quantity}, sufficient: {available}")
            return available
            
        except Exception as e:
            logger.error(f"Error checking inventory availability: {e}", exc_info=True)
            return False
    
    # ==================== HELPER TABLE OPERATIONS ====================
    
    def get_all_categories(self) -> List[Category]:
        """Get all product categories."""
        try:
            categories = self.db.query(Category).order_by(Category.name).all()
            logger.debug(f"Retrieved {len(categories)} categories")
            return categories
        except Exception as e:
            logger.error(f"Error retrieving categories: {e}", exc_info=True)
            return []
    
    def get_all_product_types(self) -> List[ProductType]:
        """Get all product types."""
        try:
            types = self.db.query(ProductType).order_by(ProductType.name).all()
            logger.debug(f"Retrieved {len(types)} product types")
            return types
        except Exception as e:
            logger.error(f"Error retrieving product types: {e}", exc_info=True)
            return []
    
    def get_all_sport_types(self) -> List[SportType]:
        """Get all sport types."""
        try:
            sports = self.db.query(SportType).order_by(SportType.name).all()
            logger.debug(f"Retrieved {len(sports)} sport types")
            return sports
        except Exception as e:
            logger.error(f"Error retrieving sport types: {e}", exc_info=True)
            return []
    
    def get_all_materials(self) -> List[Material]:
        """Get all materials."""
        try:
            materials = self.db.query(Material).order_by(Material.name).all()
            logger.debug(f"Retrieved {len(materials)} materials")
            return materials
        except Exception as e:
            logger.error(f"Error retrieving materials: {e}", exc_info=True)
            return []
    
    def create_category(self, name: str) -> Optional[Category]:
        """Create a new category."""
        try:
            category = Category(name=name)
            self.db.add(category)
            self.db.commit()
            logger.info(f"Created category: {name}")
            return category
        except IntegrityError:
            self.db.rollback()
            logger.warning(f"Category already exists: {name}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating category {name}: {e}", exc_info=True)
            return None
    
    def create_product_type(self, name: str) -> Optional[ProductType]:
        """Create a new product type."""
        try:
            product_type = ProductType(name=name)
            self.db.add(product_type)
            self.db.commit()
            logger.info(f"Created product type: {name}")
            return product_type
        except IntegrityError:
            self.db.rollback()
            logger.warning(f"Product type already exists: {name}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating product type {name}: {e}", exc_info=True)
            return None
    
    def create_sport_type(self, name: str) -> Optional[SportType]:
        """Create a new sport type."""
        try:
            sport_type = SportType(name=name)
            self.db.add(sport_type)
            self.db.commit()
            logger.info(f"Created sport type: {name}")
            return sport_type
        except IntegrityError:
            self.db.rollback()
            logger.warning(f"Sport type already exists: {name}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating sport type {name}: {e}", exc_info=True)
            return None
    
    def create_material(self, name: str) -> Optional[Material]:
        """Create a new material."""
        try:
            material = Material(name=name)
            self.db.add(material)
            self.db.commit()
            logger.info(f"Created material: {name}")
            return material
        except IntegrityError:
            self.db.rollback()
            logger.warning(f"Material already exists: {name}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating material {name}: {e}", exc_info=True)
            return None
    
    # ==================== UTILITY METHODS ====================
    
    def get_product_count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Get the total count of products matching the filters.
        
        Args:
            filters: Same filter dictionary as get_products_filtered
            
        Returns:
            int: Total count of matching products
        """
        try:
            query = self.db.query(Product)
            
            if filters:
                query = self._apply_product_filters(query, filters)
            
            count = query.count()
            logger.debug(f"Product count with filters {filters}: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Error counting products: {e}", exc_info=True)
            return 0
    
    def get_available_sizes_for_product(self, product_id: int) -> List[str]:
        """
        Get list of sizes that have inventory > 0 for a product.
        
        Args:
            product_id: Product ID
            
        Returns:
            List[str]: List of available sizes
        """
        try:
            sizes = (
                self.db.query(ProductSize.size)
                .filter(
                    and_(
                        ProductSize.product_id == product_id,
                        ProductSize.quantity > 0
                    )
                )
                .all()
            )
            
            available_sizes = [size[0] for size in sizes]
            logger.debug(f"Available sizes for product {product_id}: {available_sizes}")
            return available_sizes
            
        except Exception as e:
            logger.error(f"Error getting available sizes for product {product_id}: {e}", exc_info=True)
            return []
    
    def get_products_by_ids(self, product_ids: List[int]) -> List[Product]:
        """
        Get multiple products by their IDs.
        
        Args:
            product_ids: List of product IDs
            
        Returns:
            List[Product]: List of products
        """
        try:
            products = (
                self.db.query(Product)
                .options(
                    joinedload(Product.product_type),
                    joinedload(Product.category),
                    joinedload(Product.sport_type),
                    joinedload(Product.material),
                    joinedload(Product.sizes)
                )
                .filter(Product.id.in_(product_ids))
                .all()
            )
            
            logger.debug(f"Retrieved {len(products)} products by IDs")
            return products
            
        except Exception as e:
            logger.error(f"Error retrieving products by IDs: {e}", exc_info=True)
            return []