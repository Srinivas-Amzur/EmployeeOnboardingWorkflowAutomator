"""
Base service class for all services.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.logging import get_logger


class BaseService:
    """Base service with common functionality."""

    def __init__(self, db: AsyncSession):
        """
        Initialize service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.logger = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
