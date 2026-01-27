"""
Logging configuration and setup for the spoXpro backend.
Provides structured logging with file rotation and different log levels.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import logging.handlers
from datetime import datetime
from typing import Optional
import json

from config.settings import get_settings

settings = get_settings()


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output."""
    
    def format(self, record):
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "ip_address"):
            log_entry["ip_address"] = record.ip_address
        if hasattr(record, "endpoint"):
            log_entry["endpoint"] = record.endpoint
        if hasattr(record, "method"):
            log_entry["method"] = record.method
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "duration"):
            log_entry["duration"] = record.duration
        
        return json.dumps(log_entry, ensure_ascii=False)


class SimpleFormatter(logging.Formatter):
    """Simple formatter for console output."""
    
    def __init__(self):
        super().__init__(
            fmt=settings.log_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    structured: bool = True
) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, uses settings default)
        structured: Whether to use structured JSON logging for file output
    """
    # Use settings defaults if not provided
    log_level = log_level or settings.log_level
    log_file = log_file or settings.log_file_path
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with simple formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(SimpleFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler with rotation and structured formatting
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=settings.log_max_file_size,
            backupCount=settings.log_backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(numeric_level)
        
        if structured:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(SimpleFormatter())
        
        root_logger.addHandler(file_handler)
        
    except Exception as e:
        # If file logging fails, log to console only
        root_logger.error(f"Failed to set up file logging: {e}")
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, File: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


def log_api_request(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    request_id: Optional[str] = None
) -> None:
    """Log API request with structured data."""
    logger.info(
        f"API Request: {method} {endpoint}",
        extra={
            "method": method,
            "endpoint": endpoint,
            "user_id": user_id,
            "ip_address": ip_address,
            "request_id": request_id
        }
    )


def log_api_response(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    status_code: int,
    duration: float,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    request_id: Optional[str] = None
) -> None:
    """Log API response with structured data."""
    logger.info(
        f"API Response: {method} {endpoint} - {status_code} ({duration:.3f}s)",
        extra={
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration": duration,
            "user_id": user_id,
            "ip_address": ip_address,
            "request_id": request_id
        }
    )


def log_database_operation(
    logger: logging.Logger,
    operation: str,
    table: str,
    record_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> None:
    """Log database operation with structured data."""
    logger.info(
        f"Database {operation}: {table}" + (f" (ID: {record_id})" if record_id else ""),
        extra={
            "operation": operation,
            "table": table,
            "record_id": record_id,
            "user_id": user_id
        }
    )


def log_authentication_attempt(
    logger: logging.Logger,
    email: str,
    success: bool,
    ip_address: Optional[str] = None,
    reason: Optional[str] = None
) -> None:
    """Log authentication attempt with structured data."""
    status = "SUCCESS" if success else "FAILED"
    message = f"Authentication {status}: {email}"
    if reason:
        message += f" - {reason}"
    
    logger.info(
        message,
        extra={
            "email": email,
            "success": success,
            "ip_address": ip_address,
            "reason": reason
        }
    )


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[dict] = None,
    user_id: Optional[int] = None
) -> None:
    """Log error with structured data and context."""
    logger.error(
        f"Error: {str(error)}",
        exc_info=True,
        extra={
            "error_type": type(error).__name__,
            "context": context or {},
            "user_id": user_id
        }
    )