"""
Capa ORM del sistema (SQLAlchemy).

Uso:
    from orm import sesion, Categoria, Producto, Movimiento
"""

from .base import Base, obtener_engine, sesion
from .modelos import Categoria, Movimiento, Producto

__all__ = [
    "Base",
    "obtener_engine",
    "sesion",
    "Categoria",
    "Producto",
    "Movimiento",
]
