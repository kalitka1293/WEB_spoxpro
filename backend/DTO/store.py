"""
Product and store-related Pydantic DTO models for spoXpro backend.

These models define the request and response structures for store endpoints,
including product information, filtering, and helper table data.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum


class GenderEnum(str, Enum):
    """Enum for product gender categories."""
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"


class SizeEnum(str, Enum):
    """Enum for clothing sizes."""
    XXS = "XXS"
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"
    XXXL = "XXXL"
    XXXXL = "XXXXL"


class ProductSizeResponse(BaseModel):
    """Response model for product size information."""
    
    size: SizeEnum = Field(..., description="Clothing size")
    quantity: int = Field(..., ge=0, description="Available quantity for this size")
    
    class Config:
        schema_extra = {
            "example": {
                "size": "M",
                "quantity": 15
            }
        }


class ProductTypeResponse(BaseModel):
    """Response model for product type information."""
    
    id: int = Field(..., description="Product type unique identifier")
    name: str = Field(..., description="Product type name")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "T-Shirt"
            }
        }


class CategoryResponse(BaseModel):
    """Response model for category information."""
    
    id: int = Field(..., description="Category unique identifier")
    name: str = Field(..., description="Category name")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Men's Clothing"
            }
        }


class SportTypeResponse(BaseModel):
    """Response model for sport type information."""
    
    id: int = Field(..., description="Sport type unique identifier")
    name: str = Field(..., description="Sport type name")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Running"
            }
        }


class MaterialResponse(BaseModel):
    """Response model for material information."""
    
    id: int = Field(..., description="Material unique identifier")
    name: str = Field(..., description="Material name")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Cotton"
            }
        }


class ProductResponse(BaseModel):
    """Response model for product information."""
    
    id: int = Field(..., description="Product unique identifier")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    product_type: ProductTypeResponse = Field(..., description="Product type information")
    category: CategoryResponse = Field(..., description="Category information")
    sport_type: SportTypeResponse = Field(..., description="Sport type information")
    color: str = Field(..., description="Product color")
    gender: GenderEnum = Field(..., description="Target gender")
    brand: str = Field(..., description="Product brand")
    price: Decimal = Field(..., ge=0, description="Product price")
    reviews: List[Dict[str, Any]] = Field(default=[], description="Product reviews")
    article_number: str = Field(..., description="Unique article number")
    images: List[str] = Field(..., description="Product image URLs")
    material: MaterialResponse = Field(..., description="Material information")
    sizes: List[ProductSizeResponse] = Field(..., description="Available sizes and quantities")
    product_views: int = Field(..., ge=0, description="Number of times product was viewed")
    created_date: datetime = Field(..., description="Product creation timestamp")
    last_updated_date: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Premium Running T-Shirt",
                "description": "High-performance moisture-wicking t-shirt perfect for running",
                "product_type": {"id": 1, "name": "T-Shirt"},
                "category": {"id": 1, "name": "Men's Clothing"},
                "sport_type": {"id": 1, "name": "Running"},
                "color": "Navy Blue",
                "gender": "male",
                "brand": "spoXpro",
                "price": "29.99",
                "reviews": [
                    {"rating": 5, "comment": "Great quality!", "user": "John D."},
                    {"rating": 4, "comment": "Very comfortable", "user": "Sarah M."}
                ],
                "article_number": "SPX-RUN-001",
                "images": ["image1.jpg", "image2.jpg"],
                "material": {"id": 1, "name": "Polyester Blend"},
                "sizes": [
                    {"size": "M", "quantity": 15},
                    {"size": "L", "quantity": 10},
                    {"size": "XL", "quantity": 5}
                ],
                "product_views": 127,
                "created_date": "2024-01-01T12:00:00Z",
                "last_updated_date": "2024-01-15T10:30:00Z"
            }
        }


class ProductSummaryResponse(BaseModel):
    """Response model for product summary (used in lists)."""
    
    id: int = Field(..., description="Product unique identifier")
    name: str = Field(..., description="Product name")
    color: str = Field(..., description="Product color")
    gender: GenderEnum = Field(..., description="Target gender")
    brand: str = Field(..., description="Product brand")
    price: Decimal = Field(..., ge=0, description="Product price")
    article_number: str = Field(..., description="Unique article number")
    images: List[str] = Field(..., description="Product image URLs")
    product_views: int = Field(..., ge=0, description="Number of times product was viewed")
    available_sizes: List[SizeEnum] = Field(..., description="Available sizes (with stock > 0)")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Premium Running T-Shirt",
                "color": "Navy Blue",
                "gender": "male",
                "brand": "spoXpro",
                "price": "29.99",
                "article_number": "SPX-RUN-001",
                "images": ["image1.jpg", "image2.jpg"],
                "product_views": 127,
                "available_sizes": ["M", "L", "XL"]
            }
        }


class ProductFilterRequest(BaseModel):
    """Request model for filtering products."""
    
    category: Optional[str] = Field(None, description="Filter by category name")
    product_type: Optional[str] = Field(None, description="Filter by product type name")
    sport_type: Optional[str] = Field(None, description="Filter by sport type name")
    color: Optional[str] = Field(None, description="Filter by color")
    gender: Optional[GenderEnum] = Field(None, description="Filter by gender")
    brand: Optional[str] = Field(None, description="Filter by brand")
    min_price: Optional[Decimal] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Maximum price filter")
    size: Optional[SizeEnum] = Field(None, description="Filter by available size")
    material: Optional[str] = Field(None, description="Filter by material name")
    search: Optional[str] = Field(None, min_length=1, max_length=100, description="Search in name and description")
    sort_by: Optional[str] = Field("created_date", description="Sort field (name, price, created_date, product_views)")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc, desc)")
    page: Optional[int] = Field(1, ge=1, description="Page number for pagination")
    page_size: Optional[int] = Field(20, ge=1, le=100, description="Number of items per page")
    
    @validator('max_price')
    def validate_price_range(cls, v, values):
        """Validate that max_price is greater than min_price."""
        if v is not None and 'min_price' in values and values['min_price'] is not None:
            if v < values['min_price']:
                raise ValueError('max_price must be greater than or equal to min_price')
        return v
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validate sort_by field."""
        valid_fields = ["name", "price", "created_date", "product_views", "brand"]
        if v not in valid_fields:
            raise ValueError(f'sort_by must be one of: {", ".join(valid_fields)}')
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validate sort_order field."""
        if v not in ["asc", "desc"]:
            raise ValueError('sort_order must be either "asc" or "desc"')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "category": "Men's Clothing",
                "product_type": "T-Shirt",
                "sport_type": "Running",
                "color": "Blue",
                "gender": "male",
                "min_price": "20.00",
                "max_price": "50.00",
                "size": "M",
                "search": "running shirt",
                "sort_by": "price",
                "sort_order": "asc",
                "page": 1,
                "page_size": 20
            }
        }


class ProductListResponse(BaseModel):
    """Response model for paginated product list."""
    
    products: List[ProductSummaryResponse] = Field(..., description="List of products")
    total_count: int = Field(..., ge=0, description="Total number of products matching filters")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")
    
    class Config:
        schema_extra = {
            "example": {
                "products": [
                    {
                        "id": 1,
                        "name": "Premium Running T-Shirt",
                        "color": "Navy Blue",
                        "gender": "male",
                        "brand": "spoXpro",
                        "price": "29.99",
                        "article_number": "SPX-RUN-001",
                        "images": ["image1.jpg"],
                        "product_views": 127,
                        "available_sizes": ["M", "L", "XL"]
                    }
                ],
                "total_count": 45,
                "page": 1,
                "page_size": 20,
                "total_pages": 3,
                "has_next": True,
                "has_previous": False
            }
        }


class CreateProductRequest(BaseModel):
    """Request model for creating a new product."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: str = Field(..., min_length=1, max_length=1000, description="Product description")
    product_type_id: int = Field(..., gt=0, description="Product type ID")
    category_id: int = Field(..., gt=0, description="Category ID")
    sport_type_id: int = Field(..., gt=0, description="Sport type ID")
    color: str = Field(..., min_length=1, max_length=50, description="Product color")
    gender: GenderEnum = Field(..., description="Target gender")
    brand: str = Field(default="spoXpro", max_length=50, description="Product brand")
    price: Decimal = Field(..., gt=0, description="Product price")
    reviews: Optional[List[Dict[str, Any]]] = Field(default=[], description="Initial reviews")
    article_number: str = Field(..., min_length=1, max_length=50, description="Unique article number")
    images: List[str] = Field(..., min_items=1, description="Product image URLs")
    material_id: int = Field(..., gt=0, description="Material ID")
    sizes: List[Dict[str, Any]] = Field(..., min_items=1, description="Size and quantity information")
    
    @validator('sizes')
    def validate_sizes(cls, v):
        """Validate sizes format."""
        valid_sizes = [size.value for size in SizeEnum]
        
        for size_info in v:
            if not isinstance(size_info, dict):
                raise ValueError('Each size must be a dictionary')
            
            if 'size' not in size_info or 'quantity' not in size_info:
                raise ValueError('Each size must have "size" and "quantity" fields')
            
            if size_info['size'] not in valid_sizes:
                raise ValueError(f'Invalid size: {size_info["size"]}. Must be one of: {", ".join(valid_sizes)}')
            
            if not isinstance(size_info['quantity'], int) or size_info['quantity'] < 0:
                raise ValueError('Quantity must be a non-negative integer')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Premium Running T-Shirt",
                "description": "High-performance moisture-wicking t-shirt perfect for running",
                "product_type_id": 1,
                "category_id": 1,
                "sport_type_id": 1,
                "color": "Navy Blue",
                "gender": "male",
                "brand": "spoXpro",
                "price": "29.99",
                "article_number": "SPX-RUN-001",
                "images": ["image1.jpg", "image2.jpg"],
                "material_id": 1,
                "sizes": [
                    {"size": "M", "quantity": 15},
                    {"size": "L", "quantity": 10},
                    {"size": "XL", "quantity": 5}
                ]
            }
        }


class UpdateProductRequest(BaseModel):
    """Request model for updating a product."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, min_length=1, max_length=1000, description="Product description")
    color: Optional[str] = Field(None, min_length=1, max_length=50, description="Product color")
    price: Optional[Decimal] = Field(None, gt=0, description="Product price")
    reviews: Optional[List[Dict[str, Any]]] = Field(None, description="Product reviews")
    images: Optional[List[str]] = Field(None, min_items=1, description="Product image URLs")
    sizes: Optional[List[Dict[str, Any]]] = Field(None, description="Size and quantity updates")
    
    @validator('sizes')
    def validate_sizes(cls, v):
        """Validate sizes format if provided."""
        if v is not None:
            valid_sizes = [size.value for size in SizeEnum]
            
            for size_info in v:
                if not isinstance(size_info, dict):
                    raise ValueError('Each size must be a dictionary')
                
                if 'size' not in size_info or 'quantity' not in size_info:
                    raise ValueError('Each size must have "size" and "quantity" fields')
                
                if size_info['size'] not in valid_sizes:
                    raise ValueError(f'Invalid size: {size_info["size"]}. Must be one of: {", ".join(valid_sizes)}')
                
                if not isinstance(size_info['quantity'], int) or size_info['quantity'] < 0:
                    raise ValueError('Quantity must be a non-negative integer')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Premium Running T-Shirt",
                "price": "34.99",
                "sizes": [
                    {"size": "M", "quantity": 20},
                    {"size": "L", "quantity": 15}
                ]
            }
        }


class InventoryUpdateRequest(BaseModel):
    """Request model for updating product inventory."""
    
    size: SizeEnum = Field(..., description="Size to update")
    quantity_change: int = Field(..., description="Quantity change (positive to add, negative to subtract)")
    
    class Config:
        schema_extra = {
            "example": {
                "size": "M",
                "quantity_change": 10
            }
        }


class StoreStatisticsResponse(BaseModel):
    """Response model for store statistics."""
    
    total_products: int = Field(..., ge=0, description="Total number of products")
    total_categories: int = Field(..., ge=0, description="Total number of categories")
    total_product_types: int = Field(..., ge=0, description="Total number of product types")
    total_sport_types: int = Field(..., ge=0, description="Total number of sport types")
    total_materials: int = Field(..., ge=0, description="Total number of materials")
    most_viewed_products: List[ProductSummaryResponse] = Field(..., description="Most viewed products")
    low_stock_products: List[ProductSummaryResponse] = Field(..., description="Products with low stock")
    
    class Config:
        schema_extra = {
            "example": {
                "total_products": 150,
                "total_categories": 8,
                "total_product_types": 12,
                "total_sport_types": 6,
                "total_materials": 10,
                "most_viewed_products": [],
                "low_stock_products": []
            }
        }