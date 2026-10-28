"""
Carga de datos en segundo plano (hilos).

Las consultas a la base de datos se ejecutan en un hilo del QThreadPool, de
modo que la ventana no se congela aunque la base de datos sea grande. Cuando
la consulta termina, el resultado se entrega al hilo principal (el de la
interfaz), que es el único que puede tocar los widgets.

Reglas que sigue este módulo:
  * Cada consulta abre SU PROPIA conexión (una conexión de MySQL no se debe
    compartir entre hilos).
  * Los callbacks (al_terminar / al_error) siempre se ejecutan en el hilo
    principal, así que dentro de ellos es seguro actualizar tablas, etiquetas,
    etc.

Uso básico:

    from hilos import consultar, Cargador

    self._cargador = Cargador()

    self._cargador.cargar(
        lambda: consultar("SELECT * FROM productos"),
        lambda filas: print(len(filas)),            # se ejecuta al terminar
        lambda mensaje: print("falló:", mensaje),   # se ejecuta si hay error
    )
"""

from PySide6.QtCore import (
    QObject,
    QRunnable,
    QThreadPool,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication

from paginas.conexion import ConexionMySQL


def consultar(sql, params=None):
    """
    Ejecuta un SELECT con una conexión propia y devuelve una lista de dicts.
    Está pensada para ejecutarse DENTRO de un hilo (no toca la interfaz).
    Lanza una excepción si no hay conexión o si la consulta falla.
    """

    db = ConexionMySQL()
    conexion = db.conectar()

    if conexion is None:
        raise ConnectionError("No se pudo conectar con la base de datos.")

    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        filas = cursor.fetchall()
        cursor.close()
        return filas

    finally:
        db.cerrar()


class _Tarea(QRunnable):
    """Ejecuta una función en un hilo del pool y avisa el resultado."""

    def __init__(self, id_tarea, funcion, puente):
        super().__init__()
        self.id_tarea = id_tarea
        self.funcion = funcion
        self.puente = puente

    def run(self):

        try:
            resultado = self.funcion()

        except Exception as e:
            self.puente.listo.emit(self.id_tarea, None, str(e))

        else:
            self.puente.listo.emit(self.id_tarea, resultado, None)


class _Puente(QObject):
    """
    Vive en el hilo principal. Los hilos de trabajo emiten `listo` y Qt lo
    entrega a `_recibir` en el hilo principal (conexión en cola). Así los
    callbacks nunca se ejecutan en un hilo de trabajo.
    """

    listo = Signal(int, object, object)

    def __init__(self):

        super().__init__()

        self._callbacks = {}
        self._siguiente = 0
        self._pendientes = 0

        self.listo.connect(self._recibir)

    def lanzar(self, funcion, al_terminar, al_error):

        self._siguiente += 1
        id_tarea = self._siguiente

        self._callbacks[id_tarea] = (al_terminar, al_error)

        # Cursor de espera mientras haya consultas en curso
        self._pendientes += 1

        if self._pendientes == 1 and QApplication.instance() is not None:
            QApplication.setOverrideCursor(
                QCursor(Qt.CursorShape.BusyCursor)
            )

        QThreadPool.globalInstance().start(
            _Tarea(id_tarea, funcion, self)
        )

        return id_tarea

    @Slot(int, object, object)
    def _recibir(self, id_tarea, resultado, error):

        al_terminar, al_error = self._callbacks.pop(id_tarea, (None, None))

        self._pendientes -= 1

        if self._pendientes == 0 and QApplication.instance() is not None:
            QApplication.restoreOverrideCursor()

        if error is not None:

            if al_error is not None:
                al_error(error)
            else:
                print(f"Error en tarea en segundo plano: {error}")

        elif al_terminar is not None:
            al_terminar(resultado)


_puente = None


def ejecutar_en_hilo(funcion, al_terminar=None, al_error=None):
    """
    Ejecuta `funcion()` en un hilo. Al terminar llama a `al_terminar(resultado)`
    en el hilo principal; si falla, llama a `al_error(mensaje)`.
    """

    global _puente

    if _puente is None:
        _puente = _Puente()

    return _puente.lanzar(funcion, al_terminar, al_error)


class Cargador:
    """
    Lanza cargas en segundo plano y descarta los resultados viejos: si se
    pide una carga nueva antes de que llegue la anterior, solo se aplica la
    más reciente (así una consulta lenta no pisa datos más nuevos).
    """

    def __init__(self):
        self._contador = 0

    def cargar(self, funcion, al_terminar, al_error=None):

        self._contador += 1
        mi_numero = self._contador

        def terminado(resultado):
            if mi_numero == self._contador:
                al_terminar(resultado)

        def fallo(mensaje):
            if mi_numero == self._contador and al_error is not None:
                al_error(mensaje)

        ejecutar_en_hilo(funcion, terminado, fallo)


def esperar_hilos(milisegundos=5000):
    """Espera a que terminen las consultas pendientes (úsese al cerrar)."""

    QThreadPool.globalInstance().waitForDone(milisegundos)