# Domain models (SQLModel tables) registered on src.db's metadata.
# Import each model module here so SQLModel.metadata.create_all sees it.
from src.models import document

__all__ = ['document']
