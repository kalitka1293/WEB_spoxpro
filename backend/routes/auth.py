from fastapi import APIRouter, Request, Depends, status
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR

from service.csrf import get_csrf_token_endpoint, require_csrf
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from service.jwt_authorization import create_jwt, create_refresh_jwt, verify_refresh_jwt, get_current_user
from fastapi import Response
from logs.log_store import get_logger
from service.hash_pas import hash_password, verify_password
from db.users import add_user, get_user

logger = get_logger(__name__)


class Register(BaseModel):
    name: str
    email: str
    password: str

class Authorization(BaseModel):
    email: str
    password: str

class ForgotPassword(BaseModel):
    email: str


router_auth = APIRouter()

@router_auth.post("/register")
async def register(
    form: Register,
    request: Request,
    _: bool = Depends(require_csrf)
):
    try:
        if not form.email and not form.password and not form.name:
            return JSONResponse(status_code=HTTP_400_BAD_REQUEST, content={"error": "Введены не все обязательные поля"} )
        hash_pass = hash_password(form.password)
        result = add_user(
            name=form.name,
            email=form.email,
            password=hash_pass
        )
        if result:
            JSONResponse(status_code=HTTP_200_OK, content={"success": "Зарегистрирован"})
        else:
            return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Error"})
    except Exception as f:
        logger.error(f)
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Error"})

@router_auth.post("/authorization")
async def Authorization(
    form: Authorization,
    request: Request,
    response: Response,
    _: bool = Depends(require_csrf)
):  
    try:
        if not form:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={'error': 'Нет данных'})
        result = get_user(form.email)
        if result is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'error': 'Нет данных'})
        pass_verify = verify_password(form.password, result.password)
        if not pass_verify:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'error': 'Неверные данные'})
        payload = {"sub": str(result.id)}
        token = create_jwt(payload)
        refresh = create_refresh_jwt(payload)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=7200,
            path="/",
            secure=False
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            max_age=30 * 24 * 3600,
            path="/",
            secure=False
        )

        return {"success": True, "message": "Зарегистрирован"}
        return JSONResponse(status_code=status.HTTP_200_OK, content={"success": True, "message": "Зарегистрирован"})
    except Exception as f:
        logger.error(f)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={'error': 'Ошибка авторизации'})

@router_auth.post("/forgot_password")
async def Authorization(
    form: ForgotPassword,
    request: Request,
    _: bool = Depends(require_csrf)
):

    print('forgot_password', form)
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content={'email': 'lolkek@mail.ru'})

# Получить CSRF токен
@router_auth.get("/csrf-token")
async def csrf_token(request: Request):
    return await get_csrf_token_endpoint(request)


@router_auth.post("/refresh")
async def refresh_token(request: Request, response: Response):
    try:
        token = request.cookies.get("refresh_token")
        if not token:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Refresh token отсутствует"})

        payload = verify_refresh_jwt(token)
        if payload is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"error": "Невалидный refresh token"})

        new_access = create_jwt({"sub": payload["sub"]})
        response.set_cookie(
            key="access_token",
            value=new_access,
            httponly=True,
            max_age=7200,
            path="/",
            secure=False
        )
        return {"success": True, "message": "Токен обновлён"}
    except Exception as e:
        logger.error(f"Refresh token error: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Ошибка обновления токена"})