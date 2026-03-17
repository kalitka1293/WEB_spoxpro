import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse
from fastapi import Query
from sqlalchemy.orm import Session
from typing import Optional, List
import math
from service.csrf import get_csrf_token_endpoint, require_csrf
from pydantic import BaseModel
from fastapi import Body
from service.jwt_authorization import get_current_user, get_user_or_session
from logs.log_store import get_logger
from db.basket import add_to_basket, delete_basket_item, get_basket_by_user
from db.users import get_user
from routes.data_test import product_data, random_products, one_product
from db.products import get_products_by_list_id, to_dict_product, to_dict_product_full

logger = get_logger(__name__)
from routes.data_test import product_data, random_products, one_product
# Create router for store endpoints
from fastapi import Cookie
from db.orders import add_order, get_orders_by_user
router_basket = APIRouter(tags=["basket"])

class AddBasket(BaseModel):
    product_id: int
    size: str
    score: int

class Order(BaseModel):
    firstName: str
    lastName: str
    email: str
    phone: str
    delivery: str
    pay: str


def get_user_id_from_identity(identity):
    if identity["type"] == "guest":
        user_id = identity["session_id"]
    elif identity["type"] == "user":
        user_id = identity["data"]["sub"]
    else:
        return None
    return user_id

@router_basket.post('/order')
async def order_basket(
    order_data: Order = Body(...),
    _: bool = Depends(require_csrf),
    identity: dict = Depends(get_user_or_session)
    ):
    try:
        print(f"Получены данные заказа: {order_data}")
        user_id = get_user_id_from_identity(identity)
        if user_id is None:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                content={'error': 'Ошибка , нет пользователя'})
        if user_id is None:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                content={'error': 'Ошибка создания заказа'})

        result_basket = get_basket_by_user(user_id)
        if result_basket is None:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                content={'error': 'Ошибка создания заказа, получение товаров в корзине'})

        list_id_product = [i.product_id for i in result_basket]
        result_product = get_products_by_list_id(list_id_product)
        if result_product is None:
            raise ValueError('Ошибка получения корзины товаров пользователя')

        product_data = []
        quantity_map = {i.product_id: i.quantity for i in result_basket}
        total_amount = 0
        for i in result_product:
            qty = quantity_map.get(i.id, 1)
            price = i.price
            if i.discount and i.discount > 0:
                price = int(price * (1 - i.discount / 100))
            total_amount += price * qty
            product_data.append(to_dict_product_full(i))

        result = add_order(
            user_id=user_id,
            first_name=order_data.firstName,
            last_name=order_data.lastName,
            email=order_data.email,
            phone=order_data.phone,
            address=order_data.delivery,
            total_amount=total_amount,
            products_json=json.dumps(product_data)
        )

        if result is None:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                content={'error': 'Ошибка создания заказа, сохранение заказа'})

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True}
        )

    except Exception as f:
        logger.error(f)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={'error': 'Ошибка создания заказа'})

@router_basket.get('/score_basket')
async def score_basket(
    identity: dict = Depends(get_user_or_session)
):
    try:
        # Получить количество товаров в корзине
        user_id = get_user_id_from_identity(identity)
        if user_id is None:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                content={'error': 'Ошибка , нет пользователя'})

        result = get_basket_by_user(user_id)
        if result is None:
            raise ValueError('Ошибка получения корзины пользователя')
        data = len(result)

        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={"score": data})
    except Exception as f:
        logger.error(f)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={'error': 'Ошибка получения количества товаров в корзине'})


@router_basket.get('/get_basket')
async def get_basket(
    identity: dict = Depends(get_user_or_session)
):
    try:
        user_id = get_user_id_from_identity(identity)
        if user_id is None:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                content={'error': 'Ошибка , нет пользователя'})
        result = get_basket_by_user(user_id)
        if result is None:
            raise ValueError('Ошибка получения корзины пользователя')

        list_id_product = [i.product_id for i in result]
        result_product = get_products_by_list_id(list_id_product)
        if result_product is None:
            raise ValueError('Ошибка получения корзины товаров пользователя')

        product_data = []
        for i in result_product:
            product_data.append(to_dict_product(i, one_image=True))
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=product_data)
    except Exception as f:
        logger.error(f)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={'error': 'Ошибка получения количества товаров в корзине'})


@router_basket.delete('/delete')
async def add_basket(
    product_id: int = Query(0),
    _: bool = Depends(require_csrf),
    identity: dict = Depends(get_user_or_session)
    ):
    try:
        print(f"Получены данные для удаления ID: {product_id}")

        user_id = get_user_id_from_identity(identity)
        if user_id is None:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                content={'error': 'Ошибка добавления delete корзину, нет пользователя'})

        result = delete_basket_item(
            product_id=product_id,
            user_id=user_id
        )
        if result is None:
            raise ValueError('Товар не удален из корзины')
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True}
        )

    except Exception as f:
        logger.error(f)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={'error': 'Ошибка добавления товара в корзину'})

@router_basket.get('/get_order')
async def get_order(
    identity: dict = Depends(get_user_or_session)
):
    try:
        user_id = get_user_id_from_identity(identity)
        if user_id is None:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                content={'error': 'Ошибка, нет пользователя'})
        orders = get_orders_by_user(user_id)
        if orders is None:
            raise ValueError('Ошибка получения заказов')
        data = []
        for o in orders:
            products = json.loads(o.products_json) if o.products_json else []
            data.append({
                "id": o.id,
                "date": o.created_at.strftime("%d.%m.%Y %H:%M") if o.created_at else "",
                "total_amount": o.total_amount,
                "score": len(products),
                "status_order": o.payment_status
            })
        return JSONResponse(status_code=status.HTTP_200_OK, content=data)
    except Exception as f:
        logger.error(f)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={'error': 'Ошибка получения заказов'})

@router_basket.post('/add')
async def add_basket(
        basket_data: AddBasket = Body(...),
        _: bool = Depends(require_csrf),
        identity: dict = Depends(get_user_or_session)
):
    try:
        user_id = get_user_id_from_identity(identity)
        if user_id is None:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                content={'error': 'Ошибка добавления товара в корзину, нет пользователя'})
        result = add_to_basket(
            product_id=basket_data.product_id,
            user_id=user_id,
            size=basket_data.size,
            quantity=basket_data.score
        )
        if result is None:
            raise ValueError('Товар не добавлен в корзину')
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True}
        )
    except Exception as f:
        logger.error(f)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={'error': 'Ошибка добавления товара в корзину'})