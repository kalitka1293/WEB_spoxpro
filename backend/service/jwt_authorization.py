from datetime import datetime, timedelta
from jose import JWTError, ExpiredSignatureError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config.settings import get_settings
from logs.log_store import get_logger

logger = get_logger(__name__)
settings = get_settings()

security = HTTPBearer()


def create_jwt(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        return None


def create_refresh_jwt(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=30)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_refresh_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError as e:
        logger.error(f"Refresh JWT verification failed: {e}")
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    payload = verify_jwt(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload


async def get_user_or_session(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            return {"type": "user", "data": payload}
        except ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        except JWTError as e:
            print(f"JWTError in get_user_or_session: {e}")
            pass

    session_id = request.cookies.get("session_id")
    if session_id:
        return {"type": "guest", "session_id": session_id}

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No token or session")
