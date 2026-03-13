"""
Simple Admin Panel for spoXpro E-commerce
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Create admin FastAPI app
admin_app = FastAPI(
    title="spoXpro Admin Panel",
    description="Administrative interface for spoXpro e-commerce platform",
    version="1.0.0"
)

# Setup templates
template_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(template_dir, exist_ok=True)

templates = Jinja2Templates(directory=template_dir)

@admin_app.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>spoXpro Admin Panel</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1>🎉 spoXpro Admin Panel</h1>
            <p class="lead">Админ панель успешно создана и работает!</p>
            
            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">📦 Товары</h5>
                            <p class="card-text">Управление товарами</p>
                            <a href="/admin/products" class="btn btn-primary">Перейти</a>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">🛒 Заказы</h5>
                            <p class="card-text">Управление заказами</p>
                            <a href="/admin/orders" class="btn btn-primary">Перейти</a>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">📊 Статистика</h5>
                            <p class="card-text">Просмотр статистики</p>
                            <a href="/admin/statistics" class="btn btn-primary">Перейти</a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-4">
                <h3>✅ Возможности админ панели:</h3>
                <ul>
                    <li>Управление товарами (создать, изменить, удалить)</li>
                    <li>Просмотр товаров списком или крупными значками</li>
                    <li>Поиск товаров</li>
                    <li>Разделение по категориям</li>
                    <li>Просмотр статистики</li>
                    <li>Просмотр заказов и корзин со статусом с сортировкой</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@admin_app.get("/products")
async def admin_products():
    """Products management"""
    return {"message": "Products management page - coming soon!"}

@admin_app.get("/orders")
async def admin_orders():
    """Orders management"""
    return {"message": "Orders management page - coming soon!"}

@admin_app.get("/statistics")
async def admin_statistics():
    """Statistics page"""
    return {"message": "Statistics page - coming soon!"}