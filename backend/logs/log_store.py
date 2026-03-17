import sys
import os
import logging
import logging.handlers

from config.settings import get_settings

settings = get_settings()

_initialized = False


def setup_logging():
    global _initialized
    if _initialized:
        return
    _initialized = True

    log_file = settings.log_file_path
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    level = getattr(logging, settings.log_level.upper(), logging.WARNING)
    fmt = settings.log_format

    root = logging.getLogger()
    root.setLevel(level)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(logging.Formatter(fmt))
    root.addHandler(console)

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=settings.log_max_file_size,
        backupCount=settings.log_backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(file_handler)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        lg = logging.getLogger(name)
        lg.handlers = []
        lg.propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_api_request(logger, method, endpoint, user_id=None, ip_address=None, request_id=None):
    logger.info(f"API Request: {method} {endpoint}")


def log_api_response(logger, method, endpoint, status_code, duration, user_id=None, ip_address=None, request_id=None):
    logger.info(f"API Response: {method} {endpoint} - {status_code} ({duration:.3f}s)")
