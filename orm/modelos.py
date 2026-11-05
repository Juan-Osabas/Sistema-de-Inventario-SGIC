"""
Modelos ORM: aquí se "mapean" las tablas de MySQL a clases de Python.

    Tabla      -> Clase
    Columna    -> Atributo
    Fila       -> Objeto (una instancia de la clase)
    Llave foránea -> relationship (se navega como un atributo normal)

Nota sobre los nombres: algunos atributos tienen un nombre distinto al de la
columna (por ejemplo `Producto.stock` está mapeado a la columna
`stock_actual`). Esos nombres coinciden con los alias que ya usa el sistema
en sus consultas (`stock_actual AS stock`).

No se usa `create_all()`: las tablas ya existen en la base de datos, el ORM
solo las lee y las modifica.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Categoria(Base):
    """Tabla `categorias`."""

    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(
        "id_categoria", Integer, primary_key=True, autoincrement=True
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(255))
    estado: Mapped[str] = mapped_column(String(20), default="Activo")

    # Una categoría tiene muchos productos (lado "uno" de uno-a-muchos)
    productos: Mapped[List["Producto"]] = relationship(
        back_populates="categoria"
    )

    def __repr__(self):
        return f"<Categoria id={self.id} nombre={self.nombre!r}>"

    def como_dict(self):
        """Misma forma que usa hoy el sistema """

        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "estado": self.estado,
        }


class Producto(Base):
    """Tabla `productos`."""

    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(
        "id_producto", Integer, primary_key=True, autoincrement=True
    )
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(255))
    precio: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Atributo `stock` <-> columna `stock_actual`
    stock: Mapped[int] = mapped_column("stock_actual", Integer, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, default=0)

    # Llave foránea hacia categorias
    id_categoria: Mapped[int] = mapped_column(
        ForeignKey("categorias.id_categoria"), nullable=False
    )
    estado: Mapped[str] = mapped_column(String(20), default="Activo")

    # Muchos productos pertenecen a una categoría (lado "muchos")
    categoria: Mapped["Categoria"] = relationship(back_populates="productos")

    # Un producto tiene muchos movimientos
    movimientos: Mapped[List["Movimiento"]] = relationship(
        back_populates="producto"
    )

    def __repr__(self):
        return f"<Producto id={self.id} codigo={self.codigo!r}>"

    @property
    def stock_bajo(self):
        """Regla del sistema: stock bajo cuando stock <= stock mínimo."""

        return (self.stock or 0) <= (self.stock_minimo or 0)

    def como_dict(self):
        """
        Misma forma que devuelven hoy las consultas SQL del sistema.
        Debe usarse con la sesión abierta (lee `self.categoria`).
        """

        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "precio": self.precio,
            "stock": self.stock,
            "stock_minimo": self.stock_minimo,
            "id_categoria": self.id_categoria,
            "categoria": self.categoria.nombre,
            "estado": self.estado,
        }


class Movimiento(Base):
    """Tabla `movimientos` (entradas y salidas de inventario)."""

    __tablename__ = "movimientos"

    id: Mapped[int] = mapped_column(
        "id_movimiento", Integer, primary_key=True, autoincrement=True
    )
    id_producto: Mapped[int] = mapped_column(
        ForeignKey("productos.id_producto"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)  # Entrada / Salida
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)

    # Atributo `precio` <-> columna `precio_unitario`
    precio: Mapped[Decimal] = mapped_column(
        "precio_unitario", Numeric(10, 2), nullable=False
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    motivo: Mapped[Optional[str]] = mapped_column(String(255))

    # Atributo `stock` <-> columna `stock_resultante`
    stock: Mapped[int] = mapped_column("stock_resultante", Integer)

    producto: Mapped["Producto"] = relationship(back_populates="movimientos")

    def __repr__(self):
        return f"<Movimiento id={self.id} tipo={self.tipo!r} cantidad={self.cantidad}>"

    def como_dict(self):
        """
        Misma forma que devuelve hoy la consulta SQL de movimientos.
        Debe usarse con la sesión abierta (lee `self.producto`).
        """

        return {
            "id": self.id,
            "fecha": self.fecha,
            "codigo": self.producto.codigo,
            "producto": self.producto.nombre,
            "tipo": self.tipo,
            "cantidad": self.cantidad,
            "precio": self.precio,
            "motivo": self.motivo,
            "stock": self.stock,
        }
