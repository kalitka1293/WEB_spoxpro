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
from service.jwt_authorization import get_user_or_session
from service.csrf import require_csrf
from db.users import get_user_by_id
from logs.log_store import get_logger

logger = get_logger(__name__)

router_user = APIRouter(tags=["user"])

@router_user.get('/check')
async def check(
        user: dict = Depends(get_user_or_session)
):
    try:
        if user is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                                content={'error': 'Ошибка'})
        if user["type"] == 'guest':
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                                content={'error': 'Ошибка'})
        result = get_user_by_id(user["data"]["sub"])
        if result is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                                content={'error': 'Ошибка'})
        return JSONResponse(status_code=status.HTTP_200_OK,
                                content={'success': True})
    except Exception as f:
        logger.error(f)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={'error': 'Ошибка'})

@router_user.get('/info')
async def info(
        user: dict = Depends(get_user_or_session)
):
    try:
        if user is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                                content={'error': 'Ошибка'})
        result = get_user_by_id(user["data"]["sub"])
        if result is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                                content={'error': 'Ошибка'})
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={'name': result.name, 'email': result.email})
    except Exception as f:
        logger.error(f)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={'error': 'Ошибка'})