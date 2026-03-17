import random
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse
from fastapi import Query
from sqlalchemy.orm import Session
from typing import Optional, List
import math
import json

from logs.log_store import get_logger

from routes.data_test import product_data, random_products, one_product
from db.categories import get_all_categories
from db.products import get_all_products, get_product, to_dict_product, to_dict_product_full
from db.pickup import get_all_pickups
logger = get_logger(__name__)

# Create router for store endpoints
router_store = APIRouter(tags=["store"])


@router_store.get('/category')
async def category():
    """
        data = {
        'category_main': [{'name':'Куртки', 'id': 1}, {'name':'Джинсы', 'id': 2}, {'name':'Верхняя одежда', 'id': 3}, {'name':'Обувь', 'id': 4}],
        'category_sport': [{'name':'Фитнес', 'id': 1}, {'name':'Бег', 'id': 2}, {'name':'Прогулка', 'id': 3},],
        'category_accessories': [{'name':'Сумки', 'id': 1}, {'name':'Клатч', 'id': 2}]
    }
    """
    try:
        result = get_all_categories()
        if result is None:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                content={'error': 'Ошибка получения данных каталога'})
        category_main = []
        category_sport = []
        category_accessories = []
        for i in result:
            if i.tags == "main":
                category_main.append({'name':i.name, 'id': i.id})
            elif i.tags == "accessories":
                category_accessories.append({'name': i.name, 'id': i.id})
            elif i.tags == "sport":
                category_sport.append({'name': i.name, 'id': i.id})
            else:
                logger.error(f"Not found data category  {i}")

        data = {
            'category_main': category_main,
            'category_sport': category_sport,
            'category_accessories': category_accessories
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=data)
    except Exception as f:
        logger.error(f, exc_info=True)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={'error': 'Ошибка каталогов'})


@router_store.get('/allproduct')
async def allproduct(score: int = Query(0)):
    try:
        result = get_all_products()
        if result is None:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                content={'error': 'Ошибка получения данных товаров'})
        if score == 0:
            # Прислать все товары
            # Отдается 1 изображение
            product_data = []
            for i in result:
                product_data.append(
                    to_dict_product(i, one_image=True)
                )
            return JSONResponse(status_code=status.HTTP_200_OK, content=product_data)
        else:
            # Приоритет карточки со скидкой
            product_data_discount = []
            for i in result:
                if i.discount > 1:
                    product_data_discount.append(
                        to_dict_product(i, one_image=True)
                    )
            if len(product_data_discount) < 3:
                stop = 3 - len(product_data_discount)
                flag = 0
                for i in result:
                    flag += 1
                    product_data_discount.append(
                        to_dict_product(i, one_image=True)
                    )
                    if flag == stop:
                        break
                product_data_discount = random.sample(product_data_discount, k=3)
            return JSONResponse(status_code=status.HTTP_200_OK, content=product_data_discount)
    except Exception as f:
        logger.error(f, exc_info=True)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={'error': 'Ошибка получения данных товаров'})

@router_store.get('/product')
async def product(product_id: int = Query(0)):
    try:
        if product_id == 0:
            logger.error('Пришел ID товара 0, неожидаемо')
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                content={'error': 'Ошибка получения данных 1 товара'})
        # запрос в бд по id товару
        result = get_product(product_id)
        if result is None:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                content={'error': 'Ошибка получения данных 1 товара'})
        product_data = to_dict_product_full(result)
        return JSONResponse(status_code=status.HTTP_200_OK, content=product_data)

    except Exception as f:
        logger.error(f, exc_info=True)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={'error': 'Ошибка получения данных 1 товара'})


@router_store.get('/pickup')
async def pickup(product_id: int = Query(0)):
    try:
        result = get_all_pickups()
        if result is None:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                content={'error': 'Ошибка получения данных самовывоза'})
        data = [{"id": i.id, "address": i.address} for i in result]
        return JSONResponse(status_code=status.HTTP_200_OK, content=data)

    except Exception as f:
        logger.error(f, exc_info=True)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={'error': 'Ошибка получения данных 1 товара'})