"""
Complete Admin Panel for spoXpro E-commerce

This module provides a comprehensive admin interface for managing products,
orders, users, and viewing statistics for the spoXpro e-commerce platform.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, HTTPException, Form, Query, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import func
import logging
import os
import uuid
import shutil
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create admin FastAPI app
admin_app = FastAPI(
    title="Админ Панель spoXpro",
    description="Административный интерфейс для платформы электронной коммерции spoXpro",
    version="1.0.0"
)

# Setup templates and static files
template_dir = os.path.join(os.path.dirname(__file__), "templates")
static_dir = os.path.join(os.path.dirname(__file__), "static")
uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")

# Create directories if they don't exist
os.makedirs(template_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)

templates = Jinja2Templates(directory=template_dir)

# Mount static files
try:
    admin_app.mount("/static", StaticFiles(directory=static_dir), name="static")
    admin_app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


def save_uploaded_file(file: UploadFile) -> str:
    """Save uploaded file and return the file path"""
    try:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(uploads_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Return relative path for URL
        return f"/admin/uploads/{unique_filename}"
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Не удалось сохранить файл")


def get_db_session():
    """Get database session"""
    try:
        from db.main import get_session
        return get_session()
    except ImportError:
        logger.error("Database module not found")
        return None


class AdminService:
    """Service class for admin operations"""
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics from database"""
        try:
            session = get_db_session()
            if not session:
                return self._get_empty_stats()
            
            from db.models.product import Product
            from db.models.order import Order
            from db.models.user import User
            
            # Get product statistics
            total_products = session.query(Product).count()
            active_products = session.query(Product).filter(Product.is_active == True).count()
            
            # Get user statistics
            total_users = session.query(User).count()
            
            # Get order statistics
            total_orders = session.query(Order).count()
            total_revenue = session.query(func.sum(Order.total_amount)).scalar() or 0.0
            
            # Get recent orders
            recent_orders = session.query(Order).order_by(Order.created_date.desc()).limit(5).all()
            
            session.close()
            
            return {
                'total_products': total_products,
                'active_products': active_products,
                'total_users': total_users,
                'total_orders': total_orders,
                'total_revenue': float(total_revenue),
                'recent_orders': [self._order_to_dict(order) for order in recent_orders]
            }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return self._get_empty_stats()
    
    def _get_empty_stats(self):
        """Return empty stats when database is not available"""
        return {
            'total_products': 0,
            'active_products': 0,
            'total_users': 0,
            'total_orders': 0,
            'total_revenue': 0.0,
            'recent_orders': []
        }
    
    def _order_to_dict(self, order):
        """Convert order object to dictionary"""
        return {
            'id': order.id,
            'user_id': order.user_id,
            'total_amount': float(order.total_amount),
            'status': order.status,
            'created_date': order.created_date,
            'user': {
                'first_name': order.user.first_name if order.user else '',
                'last_name': order.user.last_name if order.user else ''
            } if hasattr(order, 'user') and order.user else None
        }

    def get_products(self, search: str = "", category: str = "", page: int = 1, per_page: int = 20):
        """Get products with filtering and pagination from database"""
        try:
            session = get_db_session()
            if not session:
                return self._get_empty_products_result()
            
            from db.models.product import Product
            from db.models.category import Category
            
            query = session.query(Product).join(Category)
            
            # Apply search filter
            if search:
                query = query.filter(Product.name.ilike(f'%{search}%'))
            
            # Apply category filter
            if category:
                query = query.filter(Category.name == category)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            products = query.offset((page - 1) * per_page).limit(per_page).all()
            
            session.close()
            
            return {
                'products': [self._product_to_dict(product) for product in products],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return self._get_empty_products_result()
    
    def _get_empty_products_result(self):
        """Return empty products result when database is not available"""
        return {
            'products': [],
            'total': 0,
            'page': 1,
            'per_page': 20,
            'total_pages': 0
        }
    
    def _product_to_dict(self, product):
        """Convert product object to dictionary"""
        return {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': float(product.price),
            'category': {
                'name': product.category.name if product.category else 'Без категории'
            },
            'category_id': product.category_id if hasattr(product, 'category_id') else None,
            'product_type_id': product.product_type_id if hasattr(product, 'product_type_id') else None,
            'sport_type_id': product.sport_type_id if hasattr(product, 'sport_type_id') else None,
            'material_id': product.material_id if hasattr(product, 'material_id') else None,
            'is_active': product.is_active,
            'image_url': product.image_url or '',
            'created_date': product.created_date if hasattr(product, 'created_date') else None
        }

    def get_orders(self, status: str = "", sort_by: str = "created_date", sort_order: str = "desc", page: int = 1, per_page: int = 20):
        """Get orders with filtering and sorting from database"""
        try:
            session = get_db_session()
            if not session:
                return self._get_empty_orders_result()
            
            from db.models.order import Order
            
            query = session.query(Order)
            
            # Apply status filter
            if status:
                query = query.filter(Order.status == status)
            
            # Apply sorting
            if sort_by == "created_date":
                order_column = Order.created_date
            elif sort_by == "total_amount":
                order_column = Order.total_amount
            elif sort_by == "status":
                order_column = Order.status
            else:
                order_column = Order.created_date
            
            if sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            orders = query.offset((page - 1) * per_page).limit(per_page).all()
            
            session.close()
            
            return {
                'orders': [self._order_to_dict(order) for order in orders],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return self._get_empty_orders_result()
    
    def _get_empty_orders_result(self):
        """Return empty orders result when database is not available"""
        return {
            'orders': [],
            'total': 0,
            'page': 1,
            'per_page': 20,
            'total_pages': 0
        }

    def get_statistics(self):
        """Get comprehensive statistics from database"""
        try:
            session = get_db_session()
            if not session:
                return self._get_empty_statistics()
            
            from db.models.product import Product
            from db.models.category import Category
            from db.models.order import Order
            from db.models.user import User
            from sqlalchemy import func
            
            # Products statistics
            products_by_category = session.query(
                Category.name, 
                func.count(Product.id).label('count')
            ).join(Product).group_by(Category.name).all()
            
            # Orders statistics
            orders_by_status = session.query(
                Order.status, 
                func.count(Order.id).label('count')
            ).group_by(Order.status).all()
            
            # Basic counts
            total_products = session.query(Product).count()
            active_products = session.query(Product).filter(Product.is_active == True).count()
            total_orders = session.query(Order).count()
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.is_active == True).count() if hasattr(User, 'is_active') else total_users
            total_revenue = session.query(func.sum(Order.total_amount)).scalar() or 0.0
            
            session.close()
            
            return {
                'products': {
                    'total': total_products,
                    'active': active_products,
                    'by_category': [{'name': name, 'count': count} for name, count in products_by_category]
                },
                'orders': {
                    'total': total_orders,
                    'by_status': [{'status': status, 'count': count} for status, count in orders_by_status],
                    'revenue': {
                        'total': float(total_revenue)
                    }
                },
                'users': {
                    'total': total_users,
                    'active': active_users
                }
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return self._get_empty_statistics()
    
    def _get_empty_statistics(self):
        """Return empty statistics when database is not available"""
        return {
            'products': {
                'total': 0,
                'active': 0,
                'by_category': []
            },
            'orders': {
                'total': 0,
                'by_status': [],
                'revenue': {
                    'total': 0.0
                }
            },
            'users': {
                'total': 0,
                'active': 0
            }
        }

    def get_categories(self):
        """Get all categories from database"""
        try:
            session = get_db_session()
            if not session:
                return []
            
            categories = session.query(Category).all()
            session.close()
            
            return [{'id': cat.id, 'name': cat.name} for cat in categories]
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []

    def get_product_types(self):
        """Get all product types from database"""
        try:
            session = get_db_session()
            if not session:
                return []
            
            from db.models.product_type import ProductType
            
            product_types = session.query(ProductType).all()
            session.close()
            
            return [{'id': pt.id, 'name': pt.name} for pt in product_types]
        except Exception as e:
            logger.error(f"Error getting product types: {e}")
            return []

    def get_sport_types(self):
        """Get all sport types from database"""
        try:
            session = get_db_session()
            if not session:
                return []
            
            from db.models.sport_type import SportType
            
            sport_types = session.query(SportType).all()
            session.close()
            
            return [{'id': st.id, 'name': st.name} for st in sport_types]
        except Exception as e:
            logger.error(f"Error getting sport types: {e}")
            return []

    def get_materials(self):
        """Get all materials from database"""
        try:
            session = get_db_session()
            if not session:
                return []
            
            from db.models.material import Material
            
            materials = session.query(Material).all()
            session.close()
            
            return [{'id': m.id, 'name': m.name} for m in materials]
        except Exception as e:
            logger.error(f"Error getting materials: {e}")
            return []


admin_service = AdminService()


# Dashboard
@admin_app.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Админ dashboard со статистикой"""
    try:
        stats = admin_service.get_dashboard_stats()
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "stats": stats,
            "title": "Панель управления"
        })
    except Exception as e:
        logger.error(f"Error in admin dashboard: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Admin Panel</title></head>
                <body>
                    <h1>spoXpro Admin Panel</h1>
                    <div class="alert alert-danger">
                        <h3>Dashboard Error</h3>
                        <p>Error loading dashboard: {str(e)}</p>
                        <p>Please check the logs for more details.</p>
                    </div>
                    <nav>
                        <a href="/admin/products">Products</a> |
                        <a href="/admin/orders">Orders</a> |
                        <a href="/admin/statistics">Statistics</a>
                    </nav>
                </body>
            </html>
            """,
            status_code=500
        )


# Products Management
@admin_app.get("/products", response_class=HTMLResponse)
async def admin_products(
    request: Request,
    page: int = Query(1, ge=1),
    search: str = Query(""),
    category: str = Query(""),
    view_mode: str = Query("list")
):
    """Страница управления товарами"""
    try:
        result = admin_service.get_products(search, category, page)
        categories = admin_service.get_categories()
        
        return templates.TemplateResponse("products.html", {
            "request": request,
            "products": result['products'],
            "categories": categories,
            "current_page": result['page'],
            "total_pages": result['total_pages'],
            "search": search,
            "category": category,
            "view_mode": view_mode,
            "title": "Управление товарами"
        })
    except Exception as e:
        logger.error(f"Error in admin products: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Products Management</title></head>
                <body>
                    <h1>Products Management</h1>
                    <div class="alert alert-danger">
                        <p>Error loading products: {str(e)}</p>
                    </div>
                    <a href="/admin/">← Back to Dashboard</a>
                </body>
            </html>
            """,
            status_code=500
        )


@admin_app.get("/products/create", response_class=HTMLResponse)
async def create_product_form(request: Request):
    """Форма создания товара"""
    try:
        categories = admin_service.get_categories()
        product_types = admin_service.get_product_types()
        sport_types = admin_service.get_sport_types()
        materials = admin_service.get_materials()
        
        return templates.TemplateResponse("product_form.html", {
            "request": request,
            "categories": categories,
            "product_types": product_types,
            "sport_types": sport_types,
            "materials": materials,
            "product": None,
            "title": "Создать товар"
        })
    except Exception as e:
        logger.error(f"Error in create product form: {e}")
        return HTMLResponse(f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


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
    image: UploadFile = File(None),
    is_active: bool = Form(False)
):
    """Создать новый товар"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.product import Product
        
        # Handle image upload
        image_url = ""
        if image and image.filename:
            image_url = save_uploaded_file(image)
        
        new_product = Product(
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            product_type_id=product_type_id,
            sport_type_id=sport_type_id,
            material_id=material_id,
            image_url=image_url,
            is_active=is_active
        )
        
        session.add(new_product)
        session.commit()
        session.close()
        
        logger.info(f"Создание товара: {name} - ₽{price}")
        return RedirectResponse(url="/admin/products", status_code=303)
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail="Не удалось создать товар")


@admin_app.post("/products/{product_id}/edit")
async def edit_product(
    product_id: int,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category_id: int = Form(...),
    product_type_id: int = Form(...),
    sport_type_id: int = Form(...),
    material_id: int = Form(...),
    image: UploadFile = File(None),
    is_active: bool = Form(False)
):
    """Редактировать товар"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.product import Product
        
        product = session.query(Product).filter(Product.id == product_id).first()
        if not product:
            session.close()
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        # Update product fields
        product.name = name
        product.description = description
        product.price = price
        product.category_id = category_id
        product.product_type_id = product_type_id
        product.sport_type_id = sport_type_id
        product.material_id = material_id
        product.is_active = is_active
        
        # Handle image upload
        if image and image.filename:
            product.image_url = save_uploaded_file(image)
        
        session.commit()
        session.close()
        
        logger.info(f"Редактирование товара ID: {product_id}")
        return RedirectResponse(url="/admin/products", status_code=303)
    except Exception as e:
        logger.error(f"Error editing product: {e}")
        raise HTTPException(status_code=500, detail="Не удалось редактировать товар")


@admin_app.get("/products/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_form(request: Request, product_id: int):
    """Форма редактирования товара"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.product import Product
        
        product = session.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            session.close()
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        product_dict = admin_service._product_to_dict(product)
        categories = admin_service.get_categories()
        product_types = admin_service.get_product_types()
        sport_types = admin_service.get_sport_types()
        materials = admin_service.get_materials()
        
        session.close()
        
        return templates.TemplateResponse("product_form.html", {
            "request": request,
            "product": product_dict,
            "categories": categories,
            "product_types": product_types,
            "sport_types": sport_types,
            "materials": materials,
            "title": f"Редактировать товар: {product_dict['name']}"
        })
    except Exception as e:
        logger.error(f"Error in edit product form: {e}")
        return HTMLResponse(f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


@admin_app.post("/products/{product_id}/delete")
async def delete_product(product_id: int):
    """Удалить товар"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.product import Product
        
        product = session.query(Product).filter(Product.id == product_id).first()
        if not product:
            session.close()
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        session.delete(product)
        session.commit()
        session.close()
        
        logger.info(f"Удаление товара ID: {product_id}")
        return RedirectResponse(url="/admin/products", status_code=303)
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        raise HTTPException(status_code=500, detail="Не удалось удалить товар")


# Orders Management
@admin_app.get("/orders", response_class=HTMLResponse)
async def admin_orders(
    request: Request,
    page: int = Query(1, ge=1),
    status: str = Query(""),
    sort_by: str = Query("created_date"),
    sort_order: str = Query("desc")
):
    """Страница управления заказами"""
    try:
        result = admin_service.get_orders(status, sort_by, sort_order, page)
        statuses = ['ожидает', 'подтвержден', 'оплачен', 'отправлен', 'завершен', 'отменен']
        
        return templates.TemplateResponse("orders.html", {
            "request": request,
            "orders": result['orders'],
            "statuses": statuses,
            "current_page": result['page'],
            "total_pages": result['total_pages'],
            "status": status,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "title": "Управление заказами"
        })
    except Exception as e:
        logger.error(f"Error in admin orders: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Orders Management</title></head>
                <body>
                    <h1>Orders Management</h1>
                    <div class="alert alert-danger">
                        <p>Error loading orders: {str(e)}</p>
                    </div>
                    <a href="/admin/">← Back to Dashboard</a>
                </body>
            </html>
            """,
            status_code=500
        )


@admin_app.get("/orders/{order_id}", response_class=HTMLResponse)
async def order_details(request: Request, order_id: int):
    """Страница деталей заказа"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.order import Order
        from db.models.order_item import OrderItem
        
        order = session.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            session.close()
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        # Get order items
        order_items = session.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        
        order_dict = admin_service._order_to_dict(order)
        order_items_list = []
        
        for item in order_items:
            order_items_list.append({
                'id': item.id,
                'product': {'name': item.product.name if item.product else f'Product #{item.product_id}'},
                'size': item.size if hasattr(item, 'size') else 'N/A',
                'quantity': item.quantity,
                'price_at_time': float(item.price_at_time)
            })
        
        session.close()
        
        return templates.TemplateResponse("order_details.html", {
            "request": request,
            "order": order_dict,
            "order_items": order_items_list,
            "title": f"Заказ №{order_id}"
        })
    except Exception as e:
        logger.error(f"Error in order details: {e}")
        return HTMLResponse(f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


@admin_app.post("/orders/{order_id}/status")
async def update_order_status(order_id: int, status: str = Form(...)):
    """Обновить статус заказа"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.order import Order
        
        order = session.query(Order).filter(Order.id == order_id).first()
        if not order:
            session.close()
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        order.status = status
        session.commit()
        session.close()
        
        logger.info(f"Обновление статуса заказа {order_id} на {status}")
        return RedirectResponse(url=f"/admin/orders/{order_id}", status_code=303)
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        raise HTTPException(status_code=500, detail="Не удалось обновить статус заказа")


# Statistics
@admin_app.get("/statistics", response_class=HTMLResponse)
async def admin_statistics(request: Request):
    """Страница статистики"""
    try:
        stats = admin_service.get_statistics()
        return templates.TemplateResponse("statistics.html", {
            "request": request,
            "stats": stats,
            "title": "Статистика"
        })
    except Exception as e:
        logger.error(f"Error in admin statistics: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Statistics</title></head>
                <body>
                    <h1>Statistics</h1>
                    <div class="alert alert-danger">
                        <p>Error loading statistics: {str(e)}</p>
                    </div>
                    <a href="/admin/">← Back to Dashboard</a>
                </body>
            </html>
            """,
            status_code=500
        )


@admin_app.get("/api/dashboard-stats")
async def dashboard_stats():
    """Get dashboard statistics API endpoint"""
    try:
        stats = admin_service.get_dashboard_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            'total_products': 0,
            'total_users': 0,
            'total_orders': 0,
            'total_revenue': 0.0
        }


# API Endpoints
@admin_app.get("/api/products/search")
async def search_products(q: str = Query("")):
    """Search products API endpoint"""
    try:
        session = get_db_session()
        if not session:
            return []
        
        from db.models.product import Product
        
        products = session.query(Product).filter(
            Product.name.ilike(f'%{q}%')
        ).limit(10).all()
        
        result = []
        for product in products:
            result.append({
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'is_active': product.is_active
            })
        
        session.close()
        return result
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        return []


@admin_app.get("/api/orders/stats")
async def order_stats():
    """Get order statistics API endpoint"""
    try:
        session = get_db_session()
        if not session:
            return {'total': 0, 'pending': 0, 'completed': 0}
        
        from db.models.order import Order
        
        total_orders = session.query(Order).count()
        pending_orders = session.query(Order).filter(Order.status == 'pending').count()
        completed_orders = session.query(Order).filter(Order.status == 'completed').count()
        
        session.close()
        
        return {
            'total': total_orders,
            'pending': pending_orders,
            'completed': completed_orders
        }
    except Exception as e:
        logger.error(f"Error getting order stats: {e}")
        return {'total': 0, 'pending': 0, 'completed': 0}


# Health check
@admin_app.get("/health")
async def admin_health():
    """Admin panel health check"""
    return {"status": "healthy", "service": "admin_panel", "version": "1.0.0"}


# Categories Management
@admin_app.get("/categories", response_class=HTMLResponse)
async def admin_categories(request: Request):
    """Страница управления категориями"""
    try:
        categories = admin_service.get_categories()
        return templates.TemplateResponse("categories.html", {
            "request": request,
            "categories": categories,
            "title": "Управление категориями"
        })
    except Exception as e:
        logger.error(f"Error in admin categories: {e}")
        return HTMLResponse(f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


@admin_app.post("/categories/create")
async def create_category(name: str = Form(...)):
    """Создать новую категорию"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        new_category = Category(name=name)
        session.add(new_category)
        session.commit()
        session.close()
        
        logger.info(f"Создание категории: {name}")
        return RedirectResponse(url="/admin/categories", status_code=303)
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        raise HTTPException(status_code=500, detail="Не удалось создать категорию")


@admin_app.post("/categories/{category_id}/edit")
async def edit_category(category_id: int, name: str = Form(...)):
    """Редактировать категорию"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.category import Category
        
        category = session.query(Category).filter(Category.id == category_id).first()
        if not category:
            session.close()
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        category.name = name
        session.commit()
        session.close()
        
        logger.info(f"Редактирование категории ID: {category_id}")
        return RedirectResponse(url="/admin/categories", status_code=303)
    except Exception as e:
        logger.error(f"Error editing category: {e}")
        raise HTTPException(status_code=500, detail="Не удалось редактировать категорию")


@admin_app.post("/categories/{category_id}/delete")
async def delete_category(category_id: int):
    """Удалить категорию"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        category = session.query(Category).filter(Category.id == category_id).first()
        if not category:
            session.close()
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        session.delete(category)
        session.commit()
        session.close()
        
        logger.info(f"Удаление категории ID: {category_id}")
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Error deleting category: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


# Attributes Management
@admin_app.get("/attributes", response_class=HTMLResponse)
async def admin_attributes(request: Request):
    """Страница управления атрибутами"""
    try:
        product_types = admin_service.get_product_types()
        sport_types = admin_service.get_sport_types()
        materials = admin_service.get_materials()
        
        return templates.TemplateResponse("attributes.html", {
            "request": request,
            "product_types": product_types,
            "sport_types": sport_types,
            "materials": materials,
            "title": "Управление атрибутами"
        })
    except Exception as e:
        logger.error(f"Error in admin attributes: {e}")
        return HTMLResponse(f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


# Product Types
@admin_app.post("/product-types/create")
async def create_product_type(name: str = Form(...)):
    """Создать новый тип товара"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.product_type import ProductType
        
        new_product_type = ProductType(name=name)
        session.add(new_product_type)
        session.commit()
        session.close()
        
        logger.info(f"Создание типа товара: {name}")
        return RedirectResponse(url="/admin/attributes", status_code=303)
    except Exception as e:
        logger.error(f"Error creating product type: {e}")
        raise HTTPException(status_code=500, detail="Не удалось создать тип товара")


@admin_app.post("/product-types/{item_id}/edit")
async def edit_product_type(item_id: int, name: str = Form(...)):
    """Редактировать тип товара"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.product_type import ProductType
        
        item = session.query(ProductType).filter(ProductType.id == item_id).first()
        if not item:
            session.close()
            raise HTTPException(status_code=404, detail="Тип товара не найден")
        
        item.name = name
        session.commit()
        session.close()
        
        logger.info(f"Редактирование типа товара ID: {item_id}")
        return RedirectResponse(url="/admin/attributes", status_code=303)
    except Exception as e:
        logger.error(f"Error editing product type: {e}")
        raise HTTPException(status_code=500, detail="Не удалось редактировать тип товара")


@admin_app.post("/product-types/{item_id}/delete")
async def delete_product_type(item_id: int):
    """Удалить тип товара"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.product_type import ProductType
        
        item = session.query(ProductType).filter(ProductType.id == item_id).first()
        if not item:
            session.close()
            raise HTTPException(status_code=404, detail="Тип товара не найден")
        
        session.delete(item)
        session.commit()
        session.close()
        
        logger.info(f"Удаление типа товара ID: {item_id}")
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Error deleting product type: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


# Sport Types
@admin_app.post("/sport-types/create")
async def create_sport_type(name: str = Form(...)):
    """Создать новый тип спорта"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.sport_type import SportType
        
        new_sport_type = SportType(name=name)
        session.add(new_sport_type)
        session.commit()
        session.close()
        
        logger.info(f"Создание типа спорта: {name}")
        return RedirectResponse(url="/admin/attributes", status_code=303)
    except Exception as e:
        logger.error(f"Error creating sport type: {e}")
        raise HTTPException(status_code=500, detail="Не удалось создать тип спорта")


@admin_app.post("/sport-types/{item_id}/edit")
async def edit_sport_type(item_id: int, name: str = Form(...)):
    """Редактировать тип спорта"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.sport_type import SportType
        
        item = session.query(SportType).filter(SportType.id == item_id).first()
        if not item:
            session.close()
            raise HTTPException(status_code=404, detail="Тип спорта не найден")
        
        item.name = name
        session.commit()
        session.close()
        
        logger.info(f"Редактирование типа спорта ID: {item_id}")
        return RedirectResponse(url="/admin/attributes", status_code=303)
    except Exception as e:
        logger.error(f"Error editing sport type: {e}")
        raise HTTPException(status_code=500, detail="Не удалось редактировать тип спорта")


@admin_app.post("/sport-types/{item_id}/delete")
async def delete_sport_type(item_id: int):
    """Удалить тип спорта"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.sport_type import SportType
        
        item = session.query(SportType).filter(SportType.id == item_id).first()
        if not item:
            session.close()
            raise HTTPException(status_code=404, detail="Тип спорта не найден")
        
        session.delete(item)
        session.commit()
        session.close()
        
        logger.info(f"Удаление типа спорта ID: {item_id}")
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Error deleting sport type: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


# Materials
@admin_app.post("/materials/create")
async def create_material(name: str = Form(...)):
    """Создать новый материал"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.material import Material
        
        new_material = Material(name=name)
        session.add(new_material)
        session.commit()
        session.close()
        
        logger.info(f"Создание материала: {name}")
        return RedirectResponse(url="/admin/attributes", status_code=303)
    except Exception as e:
        logger.error(f"Error creating material: {e}")
        raise HTTPException(status_code=500, detail="Не удалось создать материал")


@admin_app.post("/materials/{item_id}/edit")
async def edit_material(item_id: int, name: str = Form(...)):
    """Редактировать материал"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.material import Material
        
        item = session.query(Material).filter(Material.id == item_id).first()
        if not item:
            session.close()
            raise HTTPException(status_code=404, detail="Материал не найден")
        
        item.name = name
        session.commit()
        session.close()
        
        logger.info(f"Редактирование материала ID: {item_id}")
        return RedirectResponse(url="/admin/attributes", status_code=303)
    except Exception as e:
        logger.error(f"Error editing material: {e}")
        raise HTTPException(status_code=500, detail="Не удалось редактировать материал")


@admin_app.post("/materials/{item_id}/delete")
async def delete_material(item_id: int):
    """Удалить материал"""
    try:
        session = get_db_session()
        if not session:
            raise HTTPException(status_code=500, detail="Database not available")
        
        from db.models.material import Material
        
        item = session.query(Material).filter(Material.id == item_id).first()
        if not item:
            session.close()
            raise HTTPException(status_code=404, detail="Материал не найден")
        
        session.delete(item)
        session.commit()
        session.close()
        
        logger.info(f"Удаление материала ID: {item_id}")
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Error deleting material: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)