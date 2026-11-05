"""
Consultas de lectura hechas con el ORM.

Devuelven listas de diccionarios con la MISMA forma que las consultas SQL que
usa hoy el sistema, para poder reemplazar `consultar(SQL)` por estas funciones
sin cambiar el resto del código.

Cada función abre su propia sesión, así que se pueden ejecutar dentro de un
hilo de trabajo sin problemas.
"""

from sqlalchemy import select
from sqlalchemy.orm import contains_eager

from .base import sesion
from .modelos import Categoria, Movimiento, Producto


def categorias_como_dicts():
    """Todas las categorías, ordenadas por id."""

    with sesion() as s:
        consulta = select(Categoria).order_by(Categoria.id)

        return [c.como_dict() for c in s.scalars(consulta)]


def productos_como_dicts(solo_activos=False):
    """
    Productos con el nombre de su categoría (equivale a un INNER JOIN).
    `solo_activos=True` agrega el filtro estado = 'Activo'.
    """

    with sesion() as s:
        consulta = (
            select(Producto)
            .join(Producto.categoria)
            .options(contains_eager(Producto.categoria))
            .order_by(Producto.id)
        )

        if solo_activos:
            consulta = consulta.where(Producto.estado == "Activo")

        return [p.como_dict() for p in s.scalars(consulta)]


def movimientos_como_dicts(descendente=True):
    """Movimientos con el código y nombre de su producto (INNER JOIN)."""

    with sesion() as s:
        orden = Movimiento.id.desc() if descendente else Movimiento.id

        consulta = (
            select(Movimiento)
            .join(Movimiento.producto)
            .options(contains_eager(Movimiento.producto))
            .order_by(orden)
        )

        return [m.como_dict() for m in s.scalars(consulta)]
