import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse
from fastapi import Query
from sqlalchemy.orm import Session
from typing import Optional, List
import math

from logs.log_store import get_logger
from db.reviews import get_reviews_by_product

logger = get_logger(__name__)

# Create router for store endpoints
router_review = APIRouter(tags=["review"])


@router_review.get('/product_review')
async def product_review(product_id: int = Query(0)):
    try:
        reviews = get_reviews_by_product(product_id)
        if reviews is None:
            raise ValueError('Ошибка получения отзывов')
        score = len(reviews)
        if score > 0:
            summary = str(round(sum(r.rating for r in reviews if r.rating) / score, 1))
        else:
            summary = '0'
        data = {
            "score": score,
            "summary": summary,
            "reviews": [{"username": r.username, "rating": str(r.rating), "text": r.text} for r in reviews]
        }

        return JSONResponse(status_code=status.HTTP_200_OK,
                            content=data)
    except Exception as f:
        logger.error(f)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={'error': 'Ошибка получения отзывов'})