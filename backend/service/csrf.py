import secrets
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse


# Генерация токена
def generate_csrf_token() -> str:
    return secrets.token_hex(32)


# Валидация токена
async def validate_csrf(request: Request):
    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token")

    if not cookie_token or not header_token:
        raise HTTPException(400, "Missing")

    if cookie_token != header_token:
        raise HTTPException(400, "Invalid")

    return True


# Эндпоинт для получения токена
async def get_csrf_token_endpoint(request: Request):
    token = generate_csrf_token()
    response = JSONResponse({"status": "csrf cookie set"})
    response.set_cookie(key="csrf_token", value=token, httponly=False, samesite="lax")
    return response


# Dependency для роутов
async def require_csrf(request: Request):
    await validate_csrf(request)
