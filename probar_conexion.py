"""
Comprueba que la conexión a MySQL funciona con los datos del archivo .env.

Uso:
    python probar_conexion.py
"""

from paginas.conexion import ConexionMySQL


def main():

    db = ConexionMySQL()
    conexion = db.conectar()

    if conexion is None:
        print("ERROR: no se pudo conectar. Revisa los datos de tu archivo .env")
        return

    cursor = conexion.cursor()
    cursor.execute("SELECT DATABASE()")

    print(f"OK: conectado a la base de datos '{cursor.fetchone()[0]}'")

    cursor.close()
    db.cerrar()


if __name__ == "__main__":
    main()