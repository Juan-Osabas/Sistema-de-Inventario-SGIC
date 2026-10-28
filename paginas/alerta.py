import sys

import sys

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QApplication,
    QTableWidgetItem,
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTableWidget,
    QHeaderView,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QColor

from hilo.hilo import consultar, Cargador
from estilos.estilos import (
    ESTILO_PRODUCTOS,
    ESTILO_TITULO,
    ESTILO_SUBTITULO,
    ESTILO_INDICADOR_ALERTAS,
    ESTILO_INDICADOR_TITULO,
    ESTILO_INDICADOR_VALOR,
    ESTILO_INDICADOR_DESCRIPCION,
)

# Unidades por encima del stock mínimo en las que se avisa "Cerca del mínimo"
MARGEN_CERCA_MINIMO = 5

SQL_PRODUCTOS = """
    SELECT
        id_producto AS id,
        codigo,
        nombre,
        descripcion,
        precio,
        stock_actual AS stock,
        stock_minimo,
        id_categoria,
        estado
    FROM productos
    WHERE estado = 'Activo'
    ORDER BY id_producto
"""

ESTADO_BAJO = "Stock Bajo"
ESTADO_CERCA = "Cerca del mínimo"
ESTADO_NORMAL = "Stock Normal"

# estado: (color de fondo, color de texto, prioridad al ordenar)
COLORES_ESTADO = {
    ESTADO_BAJO: ("#FDEDEC", "#C0392B", 0),
    ESTADO_CERCA: ("#FEF5E7", "#CA6F1E", 1),
    ESTADO_NORMAL: ("#EAF2F8", "#2878B5", 2),
}


class Indicador(QFrame):

    def __init__(self, titulo, valor, descripcion):

        super().__init__()

        self.titulo = QLabel(titulo)
        self.valor = QLabel(valor)
        self.descripcion = QLabel(descripcion)

        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.descripcion.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(5)

        layout.addWidget(self.titulo)
        layout.addWidget(self.valor)
        layout.addWidget(self.descripcion)

        self.setLayout(layout)

        self.setMinimumHeight(130)
        self.setMaximumHeight(160)

        self.setStyleSheet(ESTILO_INDICADOR_ALERTAS)
        self.titulo.setStyleSheet(ESTILO_INDICADOR_TITULO)
        self.valor.setStyleSheet(ESTILO_INDICADOR_VALOR)
        self.descripcion.setStyleSheet(ESTILO_INDICADOR_DESCRIPCION)


class Alerta(QMainWindow):

    def __init__(self, productos=None):

        super().__init__()

        self.setStyleSheet(ESTILO_PRODUCTOS)
        self.setWindowTitle("Alertas")
        self.resize(900, 600)

        self.productos = []
        self._cargador = Cargador()

        widget = QWidget()
        self.setCentralWidget(widget)

        layout_principal = QVBoxLayout(widget)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(15)

        titulo = QLabel("Alertas de Inventario")
        titulo.setStyleSheet(ESTILO_TITULO)

        subtitulo = QLabel("Productos que requieren atención")
        subtitulo.setStyleSheet(ESTILO_SUBTITULO)

        layout_principal.addWidget(titulo)
        layout_principal.addWidget(subtitulo)

        layout_indicador = QHBoxLayout()
        layout_indicador.setSpacing(15)

        self.indicador_productos = Indicador(
            "Productos con Alertas",
            "0",
            "Productos que requieren atención"
        )

        layout_indicador.addWidget(self.indicador_productos)
        layout_principal.addLayout(layout_indicador)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels([
            "Producto",
            "Stock Actual",
            "Stock Mínimo",
            "Estado",
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabla.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tabla.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tabla.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setShowGrid(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(42)
        self.tabla.setSizeAdjustPolicy(
            QTableWidget.SizeAdjustPolicy.AdjustToContents
        )

        layout_principal.addWidget(self.tabla)

        self.cargar_productos()

    # ------------------------------------------------------------------
    # Datos
    # ------------------------------------------------------------------
    def cargar_productos(self):
        """Lee los productos en un hilo y dibuja la tabla al terminar."""

        self._cargador.cargar(
            lambda: consultar(SQL_PRODUCTOS),
            self._productos_listos,
            self._error_carga,
        )

    def _productos_listos(self, productos):

        self.productos = productos
        self.alertas()

    def _error_carga(self, mensaje):

        QMessageBox.warning(
            self,
            "Error de conexión",
            f"No se pudieron cargar los productos:\n{mensaje}"
        )

    @staticmethod
    def calcular_estado(stock_actual, stock_minimo):

        if stock_actual <= stock_minimo:
            return ESTADO_BAJO

        if stock_actual <= stock_minimo + MARGEN_CERCA_MINIMO:
            return ESTADO_CERCA

        return ESTADO_NORMAL

    # ------------------------------------------------------------------
    # Tabla
    # ------------------------------------------------------------------
    def alertas(self):

        self.tabla.setRowCount(0)

        registros = []

        for producto in self.productos:

            # `or 0` evita errores si algún valor viene vacío (NULL) de la BD
            stock_actual = producto["stock"] or 0
            stock_minimo = producto["stock_minimo"] or 0

            estado = self.calcular_estado(stock_actual, stock_minimo)

            registros.append((producto, stock_actual, stock_minimo, estado))

        # Lo más urgente primero; dentro de cada estado, orden alfabético
        registros.sort(
            key=lambda r: (
                COLORES_ESTADO[r[3]][2],
                str(r[0]["nombre"]).lower()
            )
        )

        cantidad_alertas = 0

        for producto, stock_actual, stock_minimo, estado in registros:

            if estado == ESTADO_BAJO:
                cantidad_alertas += 1

            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)

            item_producto = QTableWidgetItem(str(producto["nombre"]))
            item_stock = QTableWidgetItem(str(stock_actual))
            item_minimo = QTableWidgetItem(str(stock_minimo))
            item_estado = QTableWidgetItem(estado)

            for item in (item_stock, item_minimo, item_estado):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            fondo, texto, _ = COLORES_ESTADO[estado]

            item_estado.setBackground(QColor(fondo))
            item_estado.setForeground(QColor(texto))

            # El número de stock también se resalta cuando es crítico
            if estado == ESTADO_BAJO:
                item_stock.setForeground(QColor(texto))

            self.tabla.setItem(fila, 0, item_producto)
            self.tabla.setItem(fila, 1, item_stock)
            self.tabla.setItem(fila, 2, item_minimo)
            self.tabla.setItem(fila, 3, item_estado)

        self.indicador_productos.valor.setText(str(cantidad_alertas))

    @Slot()
    def actualizar_alertas(self):

        self.cargar_productos()


if __name__ == "__main__":

    app = QApplication(sys.argv)

    ventana = Alerta()
    ventana.show()

    sys.exit(app.exec())