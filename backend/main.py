import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid

from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic import BaseModel

# Import configuration and logging
from config.settings import get_settings
from logs.log_store import setup_logging, get_logger, log_api_request, log_api_response
from fastapi import Request, Response
import secrets
from service.csrf import require_csrf

# Get settings
settings = get_settings()
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger = get_logger(__name__)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    try:
        
        logger.info("Need inizializate DB")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Application shutdown completed")



# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.middleware("http")
async def session_middleware(request: Request, call_next):
    if request.url.path.startswith("/admin"):
        return await call_next(request)
    # Проверяем наличие session_id
    session_id = request.cookies.get("session_id")

    if not session_id:
        session_id = secrets.token_hex(16)
        response = Response()
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=False,
            max_age=2592000,
            path="/"
        )
        request.state.session_id = session_id
        return response

    request.state.session_id = session_id
    response = await call_next(request)
    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    if request.url.path.startswith("/admin"):
        return await call_next(request)
    """Middleware to log all HTTP requests and responses."""
    # Generate request ID
    request_id = str(uuid.uuid4())

    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    # Start timer
    start_time = time.time()

    # Log request
    logger = get_logger("api")
    log_api_request(
        logger=logger,
        method=request.method,
        endpoint=str(request.url.path),
        ip_address=client_ip,
        request_id=request_id
    )

    # Process request
    try:
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        log_api_response(
            logger=logger,
            method=request.method,
            endpoint=str(request.url.path),
            status_code=response.status_code,
            duration=duration,
            ip_address=client_ip,
            request_id=request_id
        )

        return response

    except Exception as e:
        # Calculate duration
        duration = time.time() - start_time

        # Log error response
        logger.error(
            f"Request failed: {request.method} {request.url.path} - {str(e)} ({duration:.3f}s)",
            extra={
                "method": request.method,
                "endpoint": str(request.url.path),
                "error": str(e),
                "duration": duration,
                "ip_address": client_ip,
                "request_id": request_id
            }
        )

        # Re-raise the exception
        raise

from starlette.middleware.sessions import SessionMiddleware

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.jwt_secret_key)


# Routes
from routes.store import router_store
from routes.review import router_review
from routes.basket import router_basket
from routes.auth import router_auth
from routes.user import router_user
from admin import setup_admin
from fastapi.staticfiles import StaticFiles
import os

app.include_router(router_store, prefix="/store")
app.include_router(router_review, prefix="/review")
app.include_router(router_basket, prefix="/basket")
app.include_router(router_auth, prefix="/auth")
app.include_router(router_user, prefix="/user")

os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/upload_dir", StaticFiles(directory="upload_dir"), name="uploads")

setup_admin(app)


def main():
    """Main function to run the application."""
    # Set up logging first
    setup_logging()
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()