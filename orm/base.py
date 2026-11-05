"""
Configuración base del ORM: conexión (Engine), sesiones y clase Base.

Conceptos:
  * Engine  -> la conexión con la base de datos (administra un "pool" de
               conexiones). Es seguro usarlo desde varios hilos.
  * Session -> el "espacio de trabajo" con el que se consultan y modifican
               objetos. NO es seguro compartirla entre hilos: cada tarea
               debe abrir la suya con `with sesion() as s:`.
  * Base    -> clase de la que heredan todos los modelos; guarda el mapa
               entre clases y tablas.
"""

import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Al importar conexion.py se lee el archivo .env y se cargan DB_HOST, DB_USER,
# etc. en os.environ. Así el ORM usa los mismos datos de conexión que el resto
# del sistema, sin duplicar contraseñas.
from paginas import conexion  # noqa: F401


class Base(DeclarativeBase):
    """Clase base de todos los modelos (Categoria, Producto, Movimiento)."""


# Engine y fábrica de sesiones: se crean la primera vez que se usa
# obtener_engine() (carga perezosa)
_engine = None
_Sesion = None


def obtener_engine():
    """Crea el Engine la primera vez y lo reutiliza después."""

    global _engine, _Sesion

    if _engine is None:

        base_datos = os.getenv("DB_NAME", "")

        if not base_datos:
            raise ValueError(
                "Falta DB_NAME. Revisa tu archivo .env (copia .env.example)."
            )

        # URL.create arma la dirección de conexión y escapa bien caracteres
        # especiales de la contraseña (@, :, /, etc.)
        url = URL.create(
            drivername="mysql+mysqlconnector",   # usa mysql-connector-python
            username=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            database=base_datos,
        )

        # pool_pre_ping: comprueba que la conexión siga viva antes de usarla
        _engine = create_engine(url, pool_pre_ping=True)

        # expire_on_commit=False: los objetos siguen usables después del commit
        _Sesion = sessionmaker(bind=_engine, expire_on_commit=False)

    return _engine


@contextmanager
def sesion():
    """
    Entrega una sesión y se encarga de cerrarla.

        with sesion() as s:
            productos = s.scalars(select(Producto)).all()

    Si todo sale bien hace commit; si hay un error hace rollback y lo vuelve
    a lanzar.
    """

    obtener_engine()

    s = _Sesion()

    try:
        yield s
        s.commit()

    except Exception:
        s.rollback()
        raise

    finally:
        s.close()
