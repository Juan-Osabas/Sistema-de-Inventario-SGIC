"""
Conexión a MySQL.

Los datos de conexión (usuario, contraseña, etc.) ya NO están escritos en el
código: se leen del archivo ".env", que puede estar junto a este archivo o en
una carpeta superior (lo normal: la raíz del proyecto). Así se puede subir el
proyecto a GitHub sin exponer la contraseña.

La clase ConexionMySQL mantiene la misma interfaz de siempre:

    db = ConexionMySQL()
    conexion = db.conectar()   # devuelve la conexión, o None si falla
    ...
    db.cerrar()
"""

import os
from pathlib import Path

import mysql.connector
from mysql.connector import Error


def _buscar_env():
    """
    Busca el archivo ".env" junto a este archivo y, si no está, en las
    carpetas superiores (hasta 3 niveles). Así el ".env" puede estar en la
    raíz del proyecto aunque conexion.py esté dentro de una subcarpeta
    (por ejemplo "paginas/").
    """

    carpeta = Path(__file__).resolve().parent

    for ruta in [carpeta, *carpeta.parents][:4]:

        candidato = ruta / ".env"

        if candidato.is_file():
            return candidato

    return None


RUTA_ENV = _buscar_env()


def _cargar_env():
    """Lee ".env" y lo carga en os.environ (sin instalar librerías extra)."""

    if RUTA_ENV is None:
        return

    for linea in RUTA_ENV.read_text(encoding="utf-8").splitlines():

        linea = linea.strip()

        if not linea or linea.startswith("#") or "=" not in linea:
            continue

        clave, valor = linea.split("=", 1)

        clave = clave.strip()
        valor = valor.strip().strip('"').strip("'")

        # Si la variable ya existe en el sistema, esa tiene prioridad
        os.environ.setdefault(clave, valor)


_cargar_env()


class ConexionMySQL:

    def __init__(self):

        self.host = os.getenv("DB_HOST", "localhost")
        self.puerto = int(os.getenv("DB_PORT", "3306"))
        self.usuario = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "")
        self.base_datos = os.getenv("DB_NAME", "")

        self.conexion = None

    def conectar(self):

        if RUTA_ENV is None:
            print(
                "No se encontró el archivo .env (se busca junto a "
                "conexion.py y en las carpetas superiores). "
                "Copia .env.example como .env y escribe tus datos."
            )
            return None

        if not self.base_datos:
            print(f"Falta DB_NAME en el archivo {RUTA_ENV}")
            return None

        try:
            self.conexion = mysql.connector.connect(
                host=self.host,
                port=self.puerto,
                user=self.usuario,
                password=self.password,
                database=self.base_datos,
            )

            return self.conexion

        except Error as e:
            print(f"Error al conectar con la base de datos: {e}")
            self.conexion = None
            return None

    def cerrar(self):

        if self.conexion is None:
            return

        try:
            if self.conexion.is_connected():
                self.conexion.close()

        except Error as e:
            print(f"Error al cerrar la conexión: {e}")

        finally:
            self.conexion = None