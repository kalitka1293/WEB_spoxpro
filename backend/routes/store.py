"""
Product and store endpoints for spoXpro backend.
Handles product catalog, search, filtering, and helper data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
import math

from db.main import get_db_session_context
from db.services.product_service import ProductService
from DTO.store import (
    ProductResponse, ProductSummaryResponse, ProductListResponse,
    ProductFilterRequest, CategoryResponse, ProductTypeResponse,
    SportTypeResponse, MaterialResponse, StoreStatisticsResponse
)
from logs.log_store import get_logger

logger = get_logger(__name__)

# Create router for store endpoints
router = APIRouter(prefix="/store", tags=["store"])


def get_product_service() -> ProductService:
    """Dependency to get ProductService instance."""
    with get_db_session_context() as db:
        return ProductService(db)


def convert_product_to_response(product) -> ProductResponse:
    """Convert Product model to ProductResponse DTO."""
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        product_type=ProductTypeResponse(
            id=product.product_type.id,
            name=product.product_type.name
        ),
        category=CategoryResponse(
            id=product.category.id,
            name=product.category.name
        ),
        sport_type=SportTypeResponse(
            id=product.sport_type.id,
            name=product.sport_type.name
        ),
        color=product.color,
        gender=product.gender,
        brand=product.brand,
        price=product.price,
        reviews=product.reviews or [],
        article_number=product.article_number,
        images=product.images or [],
        material=MaterialResponse(
            id=product.material.id,
            name=product.material.name
        ),
        sizes=[
            {"size": size.size, "quantity": size.quantity}
            for size in product.sizes
        ],
        product_views=product.product_views,
        created_date=product.created_date,
        last_updated_date=product.last_updated_date
    )


def convert_product_to_summary(product) -> ProductSummaryResponse:
    """Convert Product model to ProductSummaryResponse DTO."""
    available_sizes = [
        size.size for size in product.sizes if size.quantity > 0
    ]
    
    return ProductSummaryResponse(
        id=product.id,
        name=product.name,
        color=product.color,
        gender=product.gender,
        brand=product.brand,
        price=product.price,
        article_number=product.article_number,
        images=product.images or [],
        product_views=product.product_views,
        available_sizes=available_sizes
    )


@router.get(
    "/products",
    response_model=ProductListResponse,
    summary="Get products with filtering and pagination",
    description="Retrieve products with optional filtering, sorting, and pagination. Supports search, category filtering, price ranges, and more.",
    responses={
        200: {"description": "Products retrieved successfully"},
        400: {"description": "Invalid filter parameters"},
        500: {"description": "Internal server error"}
    }
)
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category name"),
    product_type: Optional[str] = Query(None, description="Filter by product type name"),
    sport_type: Optional[str] = Query(None, description="Filter by sport type name"),
    color: Optional[str] = Query(None, description="Filter by color"),
    gender: Optional[str] = Query(None, description="Filter by gender (male/female/unisex)"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    size: Optional[str] = Query(None, description="Filter by available size"),
    material: Optional[str] = Query(None, description="Filter by material name"),
    search: Optional[str] = Query(None, min_length=1, max_length=100, description="Search in name and description"),
    sort_by: str = Query("created_date", description="Sort field (name, price, created_date, product_views)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    product_service: ProductService = Depends(get_product_service)
):
    """Get products with filtering and pagination."""
    try:
        # Validate parameters
        if max_price is not None and min_price is not None and max_price < min_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="max_price must be greater than or equal to min_price"
            )
        
        valid_sort_fields = ["name", "price", "created_date", "product_views", "brand"]
        if sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"sort_by must be one of: {', '.join(valid_sort_fields)}"
            )
        
        if sort_order not in ["asc", "desc"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="sort_order must be either 'asc' or 'desc'"
            )
        
        # Build filters
        filters = {}
        if category:
            filters["category"] = category
        if product_type:
            filters["product_type"] = product_type
        if sport_type:
            filters["sport_type"] = sport_type
        if color:
            filters["color"] = color
        if gender:
            filters["gender"] = gender
        if brand:
            filters["brand"] = brand
        if min_price is not None:
            filters["min_price"] = min_price
        if max_price is not None:
            filters["max_price"] = max_price
        if size:
            filters["size"] = size
        if material:
            filters["material"] = material
        if search:
            filters["search"] = search
        
        # Calculate pagination
        offset = (page - 1) * page_size
        
        # Get products
        products = product_service.get_products_filtered(
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=page_size,
            offset=offset
        )
        
        # Get total count
        total_count = product_service.get_product_count(filters)
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1
        
        # Convert to response format
        product_summaries = [convert_product_to_summary(product) for product in products]
        
        logger.info(f"Retrieved {len(products)} products (page {page}/{total_pages})")
        
        return ProductListResponse(
            products=product_summaries,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving products: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products"
        )


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    summary="Get specific product by ID",
    description="Retrieve detailed information about a specific product. Increments the product view count.",
    responses={
        200: {"description": "Product retrieved successfully"},
        404: {"description": "Product not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_product(
    product_id: int,
    product_service: ProductService = Depends(get_product_service)
):
    """Get a specific product by ID and increment view count."""
    try:
        # Get product
        product = product_service.get_product_by_id(product_id)
        if not product:
            logger.warning(f"Product not found: {product_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Increment view count
        product_service.increment_product_views(product_id)
        
        # Convert to response format
        product_response = convert_product_to_response(product)
        
        logger.info(f"Retrieved product: {product.name} (ID: {product_id})")
        return product_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product"
        )


@router.get(
    "/products/article/{article_number}",
    response_model=ProductResponse,
    summary="Get product by article number",
    description="Retrieve detailed information about a product by its article number. Increments the product view count.",
    responses={
        200: {"description": "Product retrieved successfully"},
        404: {"description": "Product not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_product_by_article(
    article_number: str,
    product_service: ProductService = Depends(get_product_service)
):
    """Get a product by its article number and increment view count."""
    try:
        # Get product
        product = product_service.get_product_by_article_number(article_number)
        if not product:
            logger.warning(f"Product not found with article number: {article_number}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Increment view count
        product_service.increment_product_views(product.id)
        
        # Convert to response format
        product_response = convert_product_to_response(product)
        
        logger.info(f"Retrieved product by article number: {article_number}")
        return product_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving product by article number {article_number}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product"
        )


@router.get(
    "/search",
    response_model=ProductListResponse,
    summary="Search products",
    description="Search products by name, description, or article number with pagination.",
    responses={
        200: {"description": "Search results retrieved successfully"},
        400: {"description": "Invalid search parameters"},
        500: {"description": "Internal server error"}
    }
)
async def search_products(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    product_service: ProductService = Depends(get_product_service)
):
    """Search products by name, description, or article number."""
    try:
        # Calculate pagination
        offset = (page - 1) * page_size
        
        # Search products
        products = product_service.search_products(q, limit=page_size + offset)
        
        # Apply pagination manually since search_products doesn't support offset
        paginated_products = products[offset:offset + page_size]
        
        # Get total count (approximate)
        total_count = len(products)
        
        # Calculate pagination info
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1
        
        # Convert to response format
        product_summaries = [convert_product_to_summary(product) for product in paginated_products]
        
        logger.info(f"Search '{q}' returned {len(paginated_products)} products (page {page}/{total_pages})")
        
        return ProductListResponse(
            products=product_summaries,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )
        
    except Exception as e:
        logger.error(f"Error searching products with query '{q}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


@router.get(
    "/categories",
    response_model=List[CategoryResponse],
    summary="Get all categories",
    description="Retrieve all product categories available in the store.",
    responses={
        200: {"description": "Categories retrieved successfully"},
        500: {"description": "Internal server error"}
    }
)
async def get_categories(
    product_service: ProductService = Depends(get_product_service)
):
    """Get all product categories."""
    try:
        categories = product_service.get_all_categories()
        
        category_responses = [
            CategoryResponse(id=category.id, name=category.name)
            for category in categories
        ]
        
        logger.info(f"Retrieved {len(categories)} categories")
        return category_responses
        
    except Exception as e:
        logger.error(f"Error retrieving categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories"
        )


@router.get(
    "/product-types",
    response_model=List[ProductTypeResponse],
    summary="Get all product types",
    description="Retrieve all product types available in the store.",
    responses={
        200: {"description": "Product types retrieved successfully"},
        500: {"description": "Internal server error"}
    }
)
async def get_product_types(
    product_service: ProductService = Depends(get_product_service)
):
    """Get all product types."""
    try:
        product_types = product_service.get_all_product_types()
        
        type_responses = [
            ProductTypeResponse(id=ptype.id, name=ptype.name)
            for ptype in product_types
        ]
        
        logger.info(f"Retrieved {len(product_types)} product types")
        return type_responses
        
    except Exception as e:
        logger.error(f"Error retrieving product types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product types"
        )


@router.get(
    "/sport-types",
    response_model=List[SportTypeResponse],
    summary="Get all sport types",
    description="Retrieve all sport types available in the store.",
    responses={
        200: {"description": "Sport types retrieved successfully"},
        500: {"description": "Internal server error"}
    }
)
async def get_sport_types(
    product_service: ProductService = Depends(get_product_service)
):
    """Get all sport types."""
    try:
        sport_types = product_service.get_all_sport_types()
        
        sport_responses = [
            SportTypeResponse(id=sport.id, name=sport.name)
            for sport in sport_types
        ]
        
        logger.info(f"Retrieved {len(sport_types)} sport types")
        return sport_responses
        
    except Exception as e:
        logger.error(f"Error retrieving sport types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sport types"
        )


@router.get(
    "/materials",
    response_model=List[MaterialResponse],
    summary="Get all materials",
    description="Retrieve all materials available in the store.",
    responses={
        200: {"description": "Materials retrieved successfully"},
        500: {"description": "Internal server error"}
    }
)
async def get_materials(
    product_service: ProductService = Depends(get_product_service)
):
    """Get all materials."""
    try:
        materials = product_service.get_all_materials()
        
        material_responses = [
            MaterialResponse(id=material.id, name=material.name)
            for material in materials
        ]
        
        logger.info(f"Retrieved {len(materials)} materials")
        return material_responses
        
    except Exception as e:
        logger.error(f"Error retrieving materials: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve materials"
        )


@router.get(
    "/statistics",
    response_model=StoreStatisticsResponse,
    summary="Get store statistics",
    description="Retrieve general statistics about the store including product counts and popular items.",
    responses={
        200: {"description": "Statistics retrieved successfully"},
        500: {"description": "Internal server error"}
    }
)
async def get_store_statistics(
    product_service: ProductService = Depends(get_product_service)
):
    """Get store statistics."""
    try:
        # Get counts
        total_products = product_service.get_product_count()
        categories = product_service.get_all_categories()
        product_types = product_service.get_all_product_types()
        sport_types = product_service.get_all_sport_types()
        materials = product_service.get_all_materials()
        
        # Get most viewed products (top 10)
        most_viewed = product_service.get_products_filtered(
            sort_by="product_views",
            sort_order="desc",
            limit=10
        )
        
        # Get low stock products (products with total inventory < 10)
        all_products = product_service.get_products_filtered(limit=1000)  # Get a reasonable sample
        low_stock_products = []
        
        for product in all_products:
            total_stock = sum(size.quantity for size in product.sizes)
            if total_stock < 10 and total_stock > 0:  # Low stock but not out of stock
                low_stock_products.append(product)
        
        # Limit low stock to top 10
        low_stock_products = low_stock_products[:10]
        
        # Convert to response format
        most_viewed_summaries = [convert_product_to_summary(product) for product in most_viewed]
        low_stock_summaries = [convert_product_to_summary(product) for product in low_stock_products]
        
        statistics = StoreStatisticsResponse(
            total_products=total_products,
            total_categories=len(categories),
            total_product_types=len(product_types),
            total_sport_types=len(sport_types),
            total_materials=len(materials),
            most_viewed_products=most_viewed_summaries,
            low_stock_products=low_stock_summaries
        )
        
        logger.info("Retrieved store statistics")
        return statistics
        
    except Exception as e:
        logger.error(f"Error retrieving store statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve store statistics"
        )