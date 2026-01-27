"""
spoXpro E-commerce Backend - FastAPI Application Entry Point

A comprehensive sports clothing e-commerce platform backend built with FastAPI,
SQLAlchemy, and SQLite. Provides product management, user authentication,
shopping cart operations, and order processing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uuid

# Import configuration and logging
from config.settings import get_settings, validate_required_settings
from logs.log_store import setup_logging, get_logger, log_api_request, log_api_response
from db.main import init_database, health_check
from middleware.exception_handlers import register_exception_handlers
from docs import get_api_documentation, get_openapi_tags

# Import routers
from routes.auth import router as auth_router
from routes.user import router as user_router
from routes.store import router as store_router

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger = get_logger(__name__)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    try:
        # Validate configuration
        validate_required_settings()
        logger.info("Configuration validation successful")
        
        # Initialize database
        if init_database():
            logger.info("Database initialization successful")
        else:
            logger.error("Database initialization failed")
            raise Exception("Database initialization failed")
        
        logger.info("Application startup completed successfully")
        
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
    description=get_api_documentation()["description"],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=get_openapi_tags(),
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Register exception handlers
register_exception_handlers(app)

# Add authentication middleware
from middleware.auth_middleware import auth_middleware, admin_middleware
app.middleware("http")(auth_middleware)
app.middleware("http")(admin_middleware)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
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


# Include routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(store_router)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with application information."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint."""
    try:
        db_health = health_check()
        
        return {
            "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
            "timestamp": time.time(),
            "version": settings.app_version,
            "environment": settings.environment,
            "database": db_health
        }
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Health check failed: {e}")
        
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            }
        )


@app.get("/api-docs", tags=["root"])
async def api_documentation():
    """Get comprehensive API documentation with examples."""
    return get_api_documentation()


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