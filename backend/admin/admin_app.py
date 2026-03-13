"""
FastAPI Admin Panel for spoXpro E-commerce

This module provides a comprehensive admin interface for managing products,
orders, users, and viewing statistics for the spoXpro e-commerce platform.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Optional, Dict, Any
from datetime import datetime

from db.main import get_db_session_context
from db.models.product import Product, ProductType, Category, SportType, Material
from db.models.user import User
from db.models.order import Order, OrderItem
from db.services.product_service import ProductService
from db.services.user_service import UserService
from db.services.order_service import OrderService
from logs.log_store import get_logger

logger = get_logger(__name__)

# Create admin FastAPI app
admin_app = FastAPI(
    title="spoXpro Admin Panel",
    description="Administrative interface for spoXpro e-commerce platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Create directories if they don't exist
template_dir = os.path.join(os.path.dirname(__file__), "templates")
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(template_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)

# Mount static files
try:
    admin_app.mount("/static", StaticFiles(directory=static_dir), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


class AdminService:
    """Service class for admin operations"""
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            with get_db_session_context() as db:
                # Get basic counts
                total_products = db.query(Product).count()
                total_users = db.query(User).count()
                total_orders = db.query(Order).count()
                
                # Get recent orders
                recent_orders = db.query(Order).order_by(Order.created_date.desc()).limit(5).all()
                
                # Calculate total revenue
                total_revenue = db.query(Order).filter(Order.status.in_(['completed', 'paid'])).with_entities(
                    db.func.sum(Order.total_amount)
                ).scalar() or 0
                
                return {
                    'total_products': total_products,
                    'total_users': total_users,
                    'total_orders': total_orders,
                    'total_revenue': float(total_revenue),
                    'recent_orders': recent_orders
                }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {
                'total_products': 0,
                'total_users': 0,
                'total_orders': 0,
                'total_revenue': 0.0,
                'recent_orders': []
            }


admin_service = AdminService()


@admin_app.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard with statistics"""
    stats = admin_service.get_dashboard_stats()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "title": "Dashboard"
    })


@admin_app.get("/products", response_class=HTMLResponse)
async def admin_products(
    request: Request,
    page: int = 1,
    search: Optional[str] = None,
    category: Optional[str] = None,
    view_mode: str = "list"
):
    """Products management page"""
    try:
        with get_db_session_context() as db:
            product_service = ProductService(db)
            
            # Build query
            query = db.query(Product)
            
            # Apply search filter
            if search:
                query = query.filter(Product.name.contains(search))
            
            # Apply category filter
            if category:
                query = query.join(Category).filter(Category.name == category)
            
            # Pagination
            per_page = 20
            offset = (page - 1) * per_page
            products = query.offset(offset).limit(per_page).all()
            total_products = query.count()
            
            # Get categories for filter
            categories = db.query(Category).all()
            
            return templates.TemplateResponse("products.html", {
                "request": request,
                "products": products,
                "categories": categories,
                "current_page": page,
                "total_pages": (total_products + per_page - 1) // per_page,
                "search": search or "",
                "category": category or "",
                "view_mode": view_mode,
                "title": "Products Management"
            })
    except Exception as e:
        logger.error(f"Error in admin products: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_app.get("/products/create", response_class=HTMLResponse)
async def create_product_form(request: Request):
    """Create product form"""
    try:
        with get_db_session_context() as db:
            categories = db.query(Category).all()
            product_types = db.query(ProductType).all()
            sport_types = db.query(SportType).all()
            materials = db.query(Material).all()
            
            return templates.TemplateResponse("product_form.html", {
                "request": request,
                "categories": categories,
                "product_types": product_types,
                "sport_types": sport_types,
                "materials": materials,
                "product": None,
                "title": "Create Product"
            })
    except Exception as e:
        logger.error(f"Error in create product form: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_app.post("/products/create")
async def create_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category_id: int = Form(...),
    product_type_id: int = Form(...),
    sport_type_id: int = Form(...),
    material_id: int = Form(...),
    image_url: str = Form(""),
    is_active: bool = Form(False)
):
    """Create new product"""
    try:
        with get_db_session_context() as db:
            product_service = ProductService(db)
            
            product_data = {
                'name': name,
                'description': description,
                'price': price,
                'category_id': category_id,
                'product_type_id': product_type_id,
                'sport_type_id': sport_type_id,
                'material_id': material_id,
                'image_url': image_url,
                'is_active': is_active
            }
            
            product = product_service.create_product(product_data)
            logger.info(f"Product created: {product.name} (ID: {product.id})")
            
            return RedirectResponse(url="/admin/products", status_code=303)
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail="Failed to create product")


@admin_app.get("/orders", response_class=HTMLResponse)
async def admin_orders(
    request: Request,
    page: int = 1,
    status: Optional[str] = None,
    sort_by: str = "created_date",
    sort_order: str = "desc"
):
    """Orders management page"""
    try:
        with get_db_session_context() as db:
            # Build query
            query = db.query(Order)
            
            # Apply status filter
            if status:
                query = query.filter(Order.status == status)
            
            # Apply sorting
            if sort_order == "desc":
                query = query.order_by(getattr(Order, sort_by).desc())
            else:
                query = query.order_by(getattr(Order, sort_by).asc())
            
            # Pagination
            per_page = 20
            offset = (page - 1) * per_page
            orders = query.offset(offset).limit(per_page).all()
            total_orders = query.count()
            
            # Get unique statuses for filter
            statuses = db.query(Order.status).distinct().all()
            status_list = [s[0] for s in statuses]
            
            return templates.TemplateResponse("orders.html", {
                "request": request,
                "orders": orders,
                "statuses": status_list,
                "current_page": page,
                "total_pages": (total_orders + per_page - 1) // per_page,
                "status": status or "",
                "sort_by": sort_by,
                "sort_order": sort_order,
                "title": "Orders Management"
            })
    except Exception as e:
        logger.error(f"Error in admin orders: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@admin_app.get("/statistics", response_class=HTMLResponse)
async def admin_statistics(request: Request):
    """Statistics page"""
    try:
        with get_db_session_context() as db:
            # Get comprehensive statistics
            stats = {
                'products': {
                    'total': db.query(Product).count(),
                    'active': db.query(Product).filter(Product.is_active == True).count(),
                    'by_category': []
                },
                'orders': {
                    'total': db.query(Order).count(),
                    'by_status': [],
                    'revenue': {
                        'total': 0
                    }
                },
                'users': {
                    'total': db.query(User).count(),
                    'active': db.query(User).filter(User.is_active == True).count()
                }
            }
            
            # Products by category
            category_stats = db.query(
                Category.name,
                db.func.count(Product.id)
            ).join(Product).group_by(Category.name).all()
            stats['products']['by_category'] = [{'name': name, 'count': count} for name, count in category_stats]
            
            # Orders by status
            status_stats = db.query(
                Order.status,
                db.func.count(Order.id)
            ).group_by(Order.status).all()
            stats['orders']['by_status'] = [{'status': status, 'count': count} for status, count in status_stats]
            
            # Revenue calculation
            total_revenue = db.query(Order).filter(Order.status.in_(['completed', 'paid'])).with_entities(
                db.func.sum(Order.total_amount)
            ).scalar() or 0
            stats['orders']['revenue']['total'] = float(total_revenue)
            
            return templates.TemplateResponse("statistics.html", {
                "request": request,
                "stats": stats,
                "title": "Statistics"
            })
    except Exception as e:
        logger.error(f"Error in admin statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# API endpoints for AJAX requests
@admin_app.get("/api/dashboard-stats")
async def get_dashboard_stats():
    """Get real-time dashboard statistics"""
    try:
        stats = admin_service.get_dashboard_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard stats")


@admin_app.get("/api/products/search")
async def search_products(q: str = ""):
    """Search products API endpoint"""
    try:
        with get_db_session_context() as db:
            products = db.query(Product).filter(
                Product.name.contains(q)
            ).limit(10).all()
            
            return [
                {
                    'id': p.id,
                    'name': p.name,
                    'price': float(p.price),
                    'is_active': p.is_active
                }
                for p in products
            ]
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return []


@admin_app.post("/api/products/{product_id}/toggle-status")
async def toggle_product_status(product_id: int):
    """Toggle product active status"""
    try:
        with get_db_session_context() as db:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            product.is_active = not product.is_active
            db.commit()
            
            return {
                "success": True,
                "is_active": product.is_active,
                "message": f"Product {'activated' if product.is_active else 'deactivated'}"
            }
    except Exception as e:
        logger.error(f"Error toggling product status: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle product status")


@admin_app.put("/api/orders/{order_id}/status")
async def update_order_status(order_id: int, status: str = Form(...)):
    """Update order status"""
    try:
        with get_db_session_context() as db:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
            if status not in valid_statuses:
                raise HTTPException(status_code=400, detail="Invalid status")
            
            order.status = status
            db.commit()
            
            return {
                "success": True,
                "status": status,
                "message": f"Order status updated to {status}"
            }
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update order status")


@admin_app.delete("/api/products/{product_id}")
async def delete_product(product_id: int):
    """Delete product"""
    try:
        with get_db_session_context() as db:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            # Check if product has orders
            has_orders = db.query(OrderItem).filter(OrderItem.product_id == product_id).first()
            if has_orders:
                # Don't delete, just deactivate
                product.is_active = False
                db.commit()
                return {
                    "success": True,
                    "message": "Product deactivated (has existing orders)"
                }
            else:
                # Safe to delete
                db.delete(product)
                db.commit()
                return {
                    "success": True,
                    "message": "Product deleted successfully"
                }
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete product")