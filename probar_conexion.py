"""
Comprueba que la conexión a MySQL funciona con los datos del archivo .env.

Uso:
    python probar_conexion.py
"""

# Se usa la misma clase que el resto del sistema, así se prueba lo real
from paginas.conexion import ConexionMySQL


def conexion():
    """Intenta conectar, consulta el nombre de la base y muestra el resultado."""


    db = ConexionMySQL()
    conexion = db.conectar()

    # conectar() devuelve None si algo falló (el motivo ya se imprimió)
    if conexion is None:
        print("ERROR: no se pudo conectar. Revisa los datos de tu archivo .env")
        return

    cursor = conexion.cursor()
    # SELECT DATABASE() devuelve el nombre de la base a la que se conectó
    cursor.execute("SELECT DATABASE()")

    print(f"OK: conectado a la base de datos '{cursor.fetchone()[0]}'")

    cursor.close()
    db.cerrar()


# Solo se ejecuta al correr este archivo directamente
if __name__ == "__main__":
    conexion()