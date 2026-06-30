"""
Utility functions and helpers.
"""

import uuid
from datetime import datetime, timezone


def generate_uuid() -> str:
    """Generate UUID string."""
    return str(uuid.uuid4())


def get_current_utc_time() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


def paginate(items: list, skip: int = 0, limit: int = 100) -> tuple[list, int]:
    """
    Paginate a list of items.
    
    Args:
        items: List to paginate
        skip: Number of items to skip
        limit: Maximum items to return
        
    Returns:
        Tuple of (paginated_items, total_count)
    """
    total = len(items)
    return items[skip : skip + limit], total
