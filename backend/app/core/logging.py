"""Centralized logging configuration and request context helpers."""

from contextvars import ContextVar
import logging
import sys

from .config import get_settings

settings = get_settings()


request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
correlation_id_context: ContextVar[str] = ContextVar("correlation_id", default="-")
user_id_context: ContextVar[str] = ContextVar("user_id", default="anonymous")


class RequestContextFilter(logging.Filter):
    """Inject request-scoped fields into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = getattr(record, "request_id", request_id_context.get())
        record.correlation_id = getattr(record, "correlation_id", correlation_id_context.get())
        record.user_id = getattr(record, "user_id", user_id_context.get())
        record.method = getattr(record, "method", "-")
        record.path = getattr(record, "path", "-")
        record.status_code = getattr(record, "status_code", "-")
        record.duration_ms = getattr(record, "duration_ms", "-")
        record.client_ip = getattr(record, "client_ip", "-")
        return True


def set_request_context(request_id: str, correlation_id: str, user_id: str = "anonymous") -> None:
    """Populate request-scoped context variables for downstream logs."""
    request_id_context.set(request_id)
    correlation_id_context.set(correlation_id)
    user_id_context.set(user_id)


def clear_request_context() -> None:
    """Reset request-scoped context variables to defaults."""
    request_id_context.set("-")
    correlation_id_context.set("-")
    user_id_context.set("anonymous")


def setup_logging() -> None:
    """Configure application logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)
    root_logger.handlers = []

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)
    console_handler.addFilter(RequestContextFilter())

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s "
            "| request_id=%(request_id)s correlation_id=%(correlation_id)s "
            "user_id=%(user_id)s method=%(method)s path=%(path)s "
            "status_code=%(status_code)s duration_ms=%(duration_ms)s client_ip=%(client_ip)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)

    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
