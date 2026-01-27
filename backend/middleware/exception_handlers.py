"""
Global exception handlers for spoXpro backend.

This module provides comprehensive error handling for all types of exceptions
that can occur in the FastAPI application, ensuring consistent error responses
and proper logging of all error conditions.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import traceback
from typing import Dict, Any, Optional

from logs.log_store import get_logger

logger = get_logger(__name__)


class ErrorResponse:
    """Standard error response format for all API endpoints."""
    
    def __init__(self, error_type: str, message: str, details: Optional[Dict[str, Any]] = None, 
                 status_code: int = 500):
        self.error_type = error_type
        self.message = message
        self.details = details or {}
        self.status_code = status_code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error response to dictionary format."""
        response = {
            "error": {
                "type": self.error_type,
                "message": self.message,
                "status_code": self.status_code
            }
        }
        
        if self.details:
            response["error"]["details"] = self.details
        
        return response


def create_error_response(error_type: str, message: str, status_code: int, 
                         details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """Create a standardized JSON error response."""
    error_response = ErrorResponse(error_type, message, details, status_code)
    
    logger.error(f"API Error: {error_type} - {message} | Status: {status_code} | Details: {details}")
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.to_dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with consistent error response formatting.
    
    Args:
        request: The FastAPI request object
        exc: The HTTP exception that was raised
    
    Returns:
        JSONResponse: Standardized error response
    """
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail} | Path: {request.url.path}")
    
    # Map common HTTP status codes to error types
    error_type_mapping = {
        400: "bad_request",
        401: "unauthorized", 
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        422: "validation_error",
        429: "rate_limit_exceeded",
        500: "internal_server_error",
        502: "bad_gateway",
        503: "service_unavailable"
    }
    
    error_type = error_type_mapping.get(exc.status_code, "http_error")
    
    return create_error_response(
        error_type=error_type,
        message=str(exc.detail),
        status_code=exc.status_code,
        details={"path": str(request.url.path), "method": request.method}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors with detailed field-level error information.
    
    Args:
        request: The FastAPI request object
        exc: The validation exception that was raised
    
    Returns:
        JSONResponse: Standardized validation error response
    """
    errors_list = exc.errors()
    logger.warning(f"Validation Error: {len(errors_list)} errors | Path: {request.url.path}")
    
    # Extract detailed validation errors
    validation_errors = []
    for error in errors_list:
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        validation_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    return create_error_response(
        error_type="validation_error",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={
            "path": str(request.url.path),
            "method": request.method,
            "validation_errors": validation_errors
        }
    )


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """
    Handle Pydantic ValidationError exceptions from DTO models.
    
    Args:
        request: The FastAPI request object
        exc: The Pydantic validation exception that was raised
    
    Returns:
        JSONResponse: Standardized validation error response
    """
    logger.warning(f"Pydantic Validation Error: {len(exc.errors())} errors | Path: {request.url.path}")
    
    # Extract detailed validation errors
    validation_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        validation_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return create_error_response(
        error_type="model_validation_error",
        message="Data model validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={
            "path": str(request.url.path),
            "method": request.method,
            "validation_errors": validation_errors
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle SQLAlchemy database errors with appropriate error responses.
    
    Args:
        request: The FastAPI request object
        exc: The SQLAlchemy exception that was raised
    
    Returns:
        JSONResponse: Standardized database error response
    """
    logger.error(f"Database Error: {type(exc).__name__} - {str(exc)} | Path: {request.url.path}")
    
    # Handle specific SQLAlchemy exceptions
    if isinstance(exc, IntegrityError):
        # Database constraint violations (foreign key, unique, etc.)
        return create_error_response(
            error_type="database_constraint_violation",
            message="Database constraint violation occurred",
            status_code=status.HTTP_409_CONFLICT,
            details={
                "path": str(request.url.path),
                "method": request.method,
                "constraint_type": "integrity_constraint"
            }
        )
    
    # Generic database error
    return create_error_response(
        error_type="database_error",
        message="A database error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={
            "path": str(request.url.path),
            "method": request.method,
            "error_type": type(exc).__name__
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other unhandled exceptions with generic error response.
    
    Args:
        request: The FastAPI request object
        exc: The generic exception that was raised
    
    Returns:
        JSONResponse: Standardized generic error response
    """
    # Log the full exception with stack trace
    logger.error(f"Unhandled Exception: {type(exc).__name__} - {str(exc)} | Path: {request.url.path}")
    logger.error(f"Stack trace: {traceback.format_exc()}")
    
    return create_error_response(
        error_type="internal_server_error",
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={
            "path": str(request.url.path),
            "method": request.method,
            "exception_type": type(exc).__name__
        }
    )


# Custom business logic exceptions
class BusinessLogicError(Exception):
    """Base exception for business logic violations."""
    
    def __init__(self, message: str, error_code: str = "business_logic_error", 
                 status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(BusinessLogicError):
    """Exception for authentication failures."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "authentication_error", status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(BusinessLogicError):
    """Exception for authorization failures."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "authorization_error", status.HTTP_403_FORBIDDEN)


class ResourceNotFoundError(BusinessLogicError):
    """Exception for resource not found errors."""
    
    def __init__(self, resource_type: str, resource_id: str = None):
        message = f"{resource_type} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        super().__init__(message, "resource_not_found", status.HTTP_404_NOT_FOUND)


class InsufficientInventoryError(BusinessLogicError):
    """Exception for inventory shortage errors."""
    
    def __init__(self, product_id: int, requested_quantity: int, available_quantity: int):
        message = f"Insufficient inventory for product {product_id}: requested {requested_quantity}, available {available_quantity}"
        super().__init__(message, "insufficient_inventory", status.HTTP_409_CONFLICT)


class InvalidOperationError(BusinessLogicError):
    """Exception for invalid business operations."""
    
    def __init__(self, message: str):
        super().__init__(message, "invalid_operation", status.HTTP_400_BAD_REQUEST)


async def business_logic_exception_handler(request: Request, exc: BusinessLogicError) -> JSONResponse:
    """
    Handle custom business logic exceptions.
    
    Args:
        request: The FastAPI request object
        exc: The business logic exception that was raised
    
    Returns:
        JSONResponse: Standardized business logic error response
    """
    logger.warning(f"Business Logic Error: {exc.error_code} - {exc.message} | Path: {request.url.path}")
    
    return create_error_response(
        error_type=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details={
            "path": str(request.url.path),
            "method": request.method
        }
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    # HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    
    # Validation exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    
    # Database exceptions
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # Business logic exceptions
    app.add_exception_handler(BusinessLogicError, business_logic_exception_handler)
    app.add_exception_handler(AuthenticationError, business_logic_exception_handler)
    app.add_exception_handler(AuthorizationError, business_logic_exception_handler)
    app.add_exception_handler(ResourceNotFoundError, business_logic_exception_handler)
    app.add_exception_handler(InsufficientInventoryError, business_logic_exception_handler)
    app.add_exception_handler(InvalidOperationError, business_logic_exception_handler)
    
    # Generic exception handler (must be last)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("All exception handlers registered successfully")