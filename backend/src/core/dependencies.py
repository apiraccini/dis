from src.db import get_session

# Thin alias so endpoints import dependency from core.dependencies.
get_db = get_session

__all__ = ['get_db', 'get_session']
