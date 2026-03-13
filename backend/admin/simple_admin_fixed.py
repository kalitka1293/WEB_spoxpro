"""
Simple Admin Panel for spoXpro E-commerce
Fixed version with proper error handling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create admin FastAPI app
admin_app = FastAPI(
    title="spoXpro Admin Panel",
    description="Administrative interface for spoXpro e-commerce platform",
    version="1.0.0"
)

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "templates")
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Create directories if they don't exist
os.makedirs(template_dir, exist_ok=True)
os.makedirs(static_dir, exist_ok=True)

templates = Jinja2Templates(directory=template_dir)

# Mount static files
try:
    admin_app.mount("/static", StaticFiles(directory=static_dir), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


def get_mock_stats() -> Dict[str, Any]:
    """Get mock dashboard statistics"""
    return {
        'total_products': 25,
        'total_users': 150,
        'total_orders': 75,
        'total_revenue': 125000.50,
        'recent_orders': []
    }


@admin_app.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard with statistics"""
    try:
        stats = get_mock_stats()
        return templates.TemplateResponse("dashboard_simple.html", {
            "request": request,
            "stats": stats,
            "title": "Dashboard"
        })
    except Exception as e:
        logger.error(f"Error in admin dashboard: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Admin Panel Error</title></head>
                <body>
                    <h1>Admin Panel</h1>
                    <p>Error loading dashboard: {str(e)}</p>
                    <p>Please check the logs for more details.</p>
                </body>
            </html>
            """,
            status_code=500
        )


@admin_app.get("/products", response_class=HTMLResponse)
async def admin_products(request: Request):
    """Products management page"""
    try:
        return templates.TemplateResponse("products_simple.html", {
            "request": request,
            "products": [],
            "categories": [],
            "current_page": 1,
            "total_pages": 1,
            "search": "",
            "category": "",
            "view_mode": "grid",
            "title": "Products Management"
        })
    except Exception as e:
        logger.error(f"Error in admin products: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Products Error</title></head>
                <body>
                    <h1>Products Management</h1>
                    <p>Error loading products: {str(e)}</p>
                </body>
            </html>
            """,
            status_code=500
        )


@admin_app.get("/orders", response_class=HTMLResponse)
async def admin_orders(request: Request):
    """Orders management page"""
    try:
        return templates.TemplateResponse("orders_simple.html", {
            "request": request,
            "orders": [],
            "statuses": [],
            "current_page": 1,
            "total_pages": 1,
            "status": "",
            "sort_by": "created_date",
            "sort_order": "desc",
            "title": "Orders Management"
        })
    except Exception as e:
        logger.error(f"Error in admin orders: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Orders Error</title></head>
                <body>
                    <h1>Orders Management</h1>
                    <p>Error loading orders: {str(e)}</p>
                </body>
            </html>
            """,
            status_code=500
        )


@admin_app.get("/statistics", response_class=HTMLResponse)
async def admin_statistics(request: Request):
    """Statistics page"""
    try:
        stats = {
            'products': {
                'total': 25,
                'active': 20,
                'by_category': [
                    {'name': 'Clothing', 'count': 15},
                    {'name': 'Shoes', 'count': 10}
                ]
            },
            'orders': {
                'total': 75,
                'by_status': [
                    {'status': 'completed', 'count': 50},
                    {'status': 'pending', 'count': 20},
                    {'status': 'cancelled', 'count': 5}
                ],
                'revenue': {
                    'total': 125000.50
                }
            },
            'users': {
                'total': 150,
                'active': 140
            }
        }
        
        return templates.TemplateResponse("statistics_simple.html", {
            "request": request,
            "stats": stats,
            "title": "Statistics"
        })
    except Exception as e:
        logger.error(f"Error in admin statistics: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Statistics Error</title></head>
                <body>
                    <h1>Statistics</h1>
                    <p>Error loading statistics: {str(e)}</p>
                </body>
            </html>
            """,
            status_code=500
        )


# Health check endpoint
@admin_app.get("/health")
async def admin_health():
    """Admin panel health check"""
    return {"status": "healthy", "service": "admin_panel"}


# API endpoints
@admin_app.get("/api/dashboard-stats")
async def get_dashboard_stats():
    """Get dashboard statistics API"""
    try:
        return get_mock_stats()
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard stats")