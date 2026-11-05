"""
Comprueba que el mapeo ORM coincide con la base de datos real.
No deja nada guardado (la prueba de escritura se revierte).

Uso (desde la raíz del proyecto):
    python probar_orm.py
"""

from sqlalchemy import func, select

from orm import Categoria, Movimiento, Producto, sesion
from orm.repositorio import productos_como_dicts


def main():

    try:
        with sesion() as s:

            # 1) Conteo de filas de cada tabla mapeada
            for clase in (Categoria, Producto, Movimiento):
                total = s.scalar(select(func.count()).select_from(clase))
                print(f"{clase.__tablename__:12} -> {total} filas")

            # 2) Relaciones: de un producto se llega a su categoría y movimientos
            producto = s.scalars(select(Producto).limit(1)).first()

            if producto is not None:
                print(
                    f"\nProducto: {producto.nombre} | "
                    f"categoría: {producto.categoria.nombre} | "
                    f"movimientos: {len(producto.movimientos)} | "
                    f"stock bajo: {producto.stock_bajo}"
                )

            # 3) Misma forma de datos que usa el sistema
            filas = productos_como_dicts()
            print(f"\nproductos_como_dicts() -> {len(filas)} filas")

            if filas:
                print("Primera fila:", filas[0])

            # 4) Prueba de escritura (INSERT) que se REVIERTE
            prueba = Categoria(
                nombre="__prueba_orm__", descripcion="temporal", estado="Activo"
            )
            s.add(prueba)
            s.flush()                       # ejecuta el INSERT dentro de la transacción
            print(f"\nINSERT de prueba hecho (id = {prueba.id})")

            s.rollback()                    # lo deshace
            print("Revertido: no quedó nada guardado.")

        print("\nOK: el mapeo ORM funciona.")

    except Exception as e:
        print(f"\nERROR en el mapeo o la conexión:\n{e}")


if __name__ == "__main__":
    main()
