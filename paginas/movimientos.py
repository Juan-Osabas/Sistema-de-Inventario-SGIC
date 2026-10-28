import sys

from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDoubleSpinBox,
    QTableWidgetItem,
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QHeaderView,
    QComboBox,
    QDialog,
    QFormLayout,
    QSpinBox,
    QMessageBox,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor

from paginas.conexion import ConexionMySQL
from hilo.hilo import consultar, Cargador
from estilos.estilos import (
    ESTILO_MOVIMIENTOS,
    ESTILO_ENTRADA,
    ESTILO_SALIDA,
    ESTILO_FORMULARIO_MOVIMIENTO,
    ESTILO_TITULO,
    ESTILO_SUBTITULO,
)

COLOR_ENTRADA = "#27AE60"
COLOR_SALIDA = "#E67E22"

SQL_PRODUCTOS = """
    SELECT
        p.id_producto AS id,
        p.codigo,
        p.nombre,
        p.descripcion,
        p.precio,
        p.stock_actual AS stock,
        p.stock_minimo,
        p.id_categoria,
        c.nombre AS categoria,
        p.estado
    FROM productos p
    INNER JOIN categorias c
        ON p.id_categoria = c.id_categoria
    WHERE p.estado = 'Activo'
    ORDER BY p.id_producto
"""

SQL_MOVIMIENTOS = """
    SELECT
        m.id_movimiento AS id,
        m.fecha,
        p.codigo,
        p.nombre AS producto,
        m.tipo,
        m.cantidad,
        m.precio_unitario AS precio,
        m.motivo,
        m.stock_resultante AS stock
    FROM movimientos m
    INNER JOIN productos p
        ON m.id_producto = p.id_producto
    ORDER BY m.id_movimiento DESC
"""


def crear_botones(dialogo):
    """Botones Guardar / Cancelar en español, conectados al diálogo."""

    botones = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Save
        | QDialogButtonBox.StandardButton.Cancel
    )
    botones.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
    botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")

    botones.accepted.connect(dialogo.guardar)
    botones.rejected.connect(dialogo.reject)

    return botones


class FormularioEntrada(QDialog):

    def __init__(self, productos, parent=None):

        super().__init__(parent)
        self.setStyleSheet(ESTILO_FORMULARIO_MOVIMIENTO)

        self.setWindowTitle("Registrar Entrada")
        self.setModal(True)

        self.productos = productos
        self.datos = None

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(15)

        titulo = QLabel("Registrar entrada de producto")
        titulo.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #2878B5;
        """)
        layout_principal.addWidget(titulo)

        formulario = QFormLayout()
        formulario.setSpacing(12)

        self.producto = QComboBox()

        for producto in self.productos:
            self.producto.addItem(producto["nombre"])

        self.producto.currentIndexChanged.connect(self.mostrar_stock)
        formulario.addRow("Producto:", self.producto)

        self.stock_actual = QLabel("0")
        formulario.addRow("Stock actual:", self.stock_actual)

        self.cantidad = QSpinBox()
        self.cantidad.setRange(1, 999999)
        formulario.addRow("Cantidad:", self.cantidad)

        self.precio = QDoubleSpinBox()
        self.precio.setRange(0.01, 999999999.99)
        self.precio.setDecimals(2)
        self.precio.setPrefix("C$ ")
        self.precio.setSingleStep(0.50)
        formulario.addRow("Precio de compra:", self.precio)

        self.motivo = QLineEdit()
        self.motivo.setPlaceholderText("Ej. Compra a proveedor")
        formulario.addRow("Motivo:", self.motivo)

        layout_principal.addLayout(formulario)
        layout_principal.addWidget(crear_botones(self))

        self.mostrar_stock()

    def mostrar_stock(self):

        indice = self.producto.currentIndex()

        if 0 <= indice < len(self.productos):
            self.stock_actual.setText(str(self.productos[indice]["stock"]))

    def guardar(self):

        indice = self.producto.currentIndex()

        if indice < 0:
            QMessageBox.warning(
                self, "Producto", "Debe seleccionar un producto."
            )
            return

        if self.precio.value() <= 0:
            QMessageBox.warning(
                self, "Precio", "Debe ingresar un precio de compra válido."
            )
            self.precio.setFocus()
            return

        if not self.motivo.text().strip():
            QMessageBox.warning(
                self, "Motivo", "Debe ingresar el motivo de la entrada."
            )
            self.motivo.setFocus()
            return

        self.datos = {
            "producto": self.productos[indice],
            "cantidad": self.cantidad.value(),
            "precio": self.precio.value(),
            "motivo": self.motivo.text().strip(),
        }

        self.accept()


class FormularioSalida(QDialog):

    def __init__(self, productos, parent=None):

        super().__init__(parent)
        self.setStyleSheet(ESTILO_FORMULARIO_MOVIMIENTO)

        self.setWindowTitle("Registrar Salida")
        self.setModal(True)

        self.productos = productos
        self.datos = None

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(15)

        titulo = QLabel("Registrar salida de producto")
        titulo.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #E67E22;
        """)
        layout_principal.addWidget(titulo)

        formulario = QFormLayout()
        formulario.setSpacing(12)

        self.producto = QComboBox()

        for producto in self.productos:
            self.producto.addItem(producto["nombre"])

        formulario.addRow("Producto:", self.producto)

        self.stock_actual = QLabel("0")
        formulario.addRow("Stock actual:", self.stock_actual)

        self.precio = QLabel("C$ 0.00")
        formulario.addRow("Precio de venta:", self.precio)

        self.cantidad = QSpinBox()
        self.cantidad.setRange(1, 999999)
        formulario.addRow("Cantidad:", self.cantidad)

        self.motivo = QLineEdit()
        self.motivo.setPlaceholderText("Ej. Venta")
        formulario.addRow("Motivo:", self.motivo)

        layout_principal.addLayout(formulario)
        layout_principal.addWidget(crear_botones(self))

        # Se conecta después de crear `cantidad`, que mostrar_datos necesita
        self.producto.currentIndexChanged.connect(self.mostrar_datos)

        self.mostrar_datos()

    def mostrar_datos(self):

        indice = self.producto.currentIndex()

        if 0 <= indice < len(self.productos):

            producto = self.productos[indice]
            stock = producto["stock"] or 0

            self.stock_actual.setText(str(stock))
            self.precio.setText(f'C$ {producto["precio"]:.2f}')

            # No permite elegir más unidades de las disponibles
            self.cantidad.setMaximum(max(stock, 1))

    def guardar(self):

        indice = self.producto.currentIndex()

        if indice < 0:
            QMessageBox.warning(
                self, "Producto", "Debe seleccionar un producto."
            )
            return

        producto = self.productos[indice]
        cantidad = self.cantidad.value()

        if cantidad > (producto["stock"] or 0):
            QMessageBox.warning(
                self,
                "Stock insuficiente",
                f'No puede retirar {cantidad} unidades.\n\n'
                f'Producto: {producto["nombre"]}\n'
                f'Stock disponible: {producto["stock"]}'
            )
            return

        if not self.motivo.text().strip():
            QMessageBox.warning(
                self, "Motivo", "Debe ingresar el motivo de la salida."
            )
            self.motivo.setFocus()
            return

        self.datos = {
            "producto": producto,
            "cantidad": cantidad,
            "precio": producto["precio"],
            "motivo": self.motivo.text().strip(),
        }

        self.accept()


class Movimientos(QMainWindow):

    movimiento_registrado = Signal(dict)
    movimientos_cargados = Signal()

    def __init__(self, productos=None):

        super().__init__()
        self.setStyleSheet(ESTILO_MOVIMIENTOS)

        self.setWindowTitle("Movimientos")
        self.resize(1000, 650)

        self.productos = []
        self.movimientos = []

        self.db = ConexionMySQL()  # solo para guardar movimientos

        self._cargador_productos = Cargador()
        self._cargador_movimientos = Cargador()
        self._abriendo_formulario = False

        widget = QWidget()
        self.setCentralWidget(widget)

        layout_principal = QVBoxLayout(widget)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(15)

        titulo = QLabel("Movimientos")
        subtitulo = QLabel("Registros de entradas y salidas del inventario")

        titulo.setStyleSheet(ESTILO_TITULO)
        subtitulo.setStyleSheet(ESTILO_SUBTITULO)

        layout_principal.addWidget(titulo)
        layout_principal.addWidget(subtitulo)

        layout_buscar = QHBoxLayout()

        btn_entrada = QPushButton("+ Entrada")
        btn_entrada.setStyleSheet(ESTILO_ENTRADA)
        btn_entrada.clicked.connect(self.registrar_entrada)

        btn_salida = QPushButton("- Salida")
        btn_salida.setStyleSheet(ESTILO_SALIDA)
        btn_salida.clicked.connect(self.registrar_salida)

        label_buscar = QLabel("Buscar Movimiento:")

        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText(
            "Buscar producto, tipo, usuario o motivo..."
        )
        self.buscar.setClearButtonEnabled(True)
        self.buscar.textChanged.connect(self.aplicar_filtros)

        self.fecha = QComboBox()
        self.fecha.addItems([
            "Todas las fechas",
            "Hoy",
            "Ayer",
            "Últimos 7 días",
            "Este mes",
            "Mes pasado",
        ])
        self.fecha.currentTextChanged.connect(self.aplicar_filtros)

        layout_buscar.addWidget(btn_entrada)
        layout_buscar.addWidget(btn_salida)
        layout_buscar.addWidget(label_buscar)
        layout_buscar.addWidget(self.buscar)
        layout_buscar.addWidget(self.fecha)

        layout_principal.addLayout(layout_buscar)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "Fecha",
            "Producto",
            "Tipo",
            "Cantidad",
            "Precio",
            "Stock",
            "Usuario",
            "Motivo",
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
        self.tabla.verticalHeader().setVisible(False)

        layout_principal.addWidget(self.tabla)

        self.cargar_productos()
        self.cargar_movimientos()

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------
    def _conectar_o_avisar(self):

        conexion = self.db.conectar()

        if conexion is None:
            QMessageBox.critical(
                self,
                "Error de conexión",
                "No se pudo conectar con la base de datos."
            )

        return conexion

    def cargar_productos(self, al_terminar=None):
        """Lee los productos en un hilo; `al_terminar` se ejecuta al llegar."""

        self._cargador_productos.cargar(
            lambda: consultar(SQL_PRODUCTOS),
            lambda filas: self._productos_listos(filas, al_terminar),
            self._error_carga_productos,
        )

    def _productos_listos(self, datos, al_terminar=None):

        self.productos = [
            {
                "id": p["id"],
                "codigo": p["codigo"],
                "nombre": p["nombre"],
                "descripcion": p["descripcion"],
                "precio": float(p["precio"] or 0),
                "stock": p["stock"] or 0,
                "stock_minimo": p["stock_minimo"],
                "id_categoria": p["id_categoria"],
                "categoria": p["categoria"],
                "estado": p["estado"],
            }
            for p in datos
        ]

        if al_terminar is not None:
            al_terminar()

    def _error_carga_productos(self, mensaje):

        self._abriendo_formulario = False

        QMessageBox.critical(
            self,
            "Error",
            f"No se pudieron cargar los productos:\n{mensaje}"
        )

    def cargar_movimientos(self, al_terminar=None):
        """Lee los movimientos en un hilo y refresca la tabla al terminar."""

        self._cargador_movimientos.cargar(
            lambda: consultar(SQL_MOVIMIENTOS),
            lambda filas: self._movimientos_listos(filas, al_terminar),
            self._error_carga_movimientos,
        )

    def _movimientos_listos(self, datos, al_terminar=None):

        self.movimientos = []

        for movimiento in datos:

            fecha = movimiento["fecha"]

            if hasattr(fecha, "strftime"):
                fecha = fecha.strftime("%d-%m-%Y")

            self.movimientos.append({
                "id": movimiento["id"],
                "fecha": str(fecha),
                "codigo": movimiento["codigo"],
                "producto": movimiento["producto"],
                "tipo": movimiento["tipo"],
                "cantidad": movimiento["cantidad"],
                "stock": movimiento["stock"],
                "precio": float(movimiento["precio"] or 0),
                "usuario": "Admin",
                "motivo": movimiento["motivo"] or "",
            })

        self.actualizar_tabla()
        self.movimientos_cargados.emit()

        if al_terminar is not None:
            al_terminar()

    def _error_carga_movimientos(self, mensaje):

        QMessageBox.critical(
            self,
            "Error",
            f"No se pudieron cargar los movimientos:\n{mensaje}"
        )

    # ------------------------------------------------------------------
    # Tabla
    # ------------------------------------------------------------------
    def actualizar_tabla(self):

        self.tabla.setRowCount(0)

        for movimiento in self.movimientos:

            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)

            valores = [
                movimiento["fecha"],
                movimiento["producto"],
                movimiento["tipo"],
                str(movimiento["cantidad"]),
                f'C$ {movimiento["precio"]:.2f}',
                str(movimiento["stock"]),
                movimiento["usuario"],
                movimiento["motivo"],
            ]

            for columna, valor in enumerate(valores):

                item = QTableWidgetItem(valor)

                if columna in (3, 5):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if columna == 2:
                    color = (
                        COLOR_ENTRADA
                        if movimiento["tipo"] == "Entrada"
                        else COLOR_SALIDA
                    )
                    item.setForeground(QColor(color))

                self.tabla.setItem(fila, columna, item)

        self.aplicar_filtros()

    # ------------------------------------------------------------------
    # Registro de movimientos
    # ------------------------------------------------------------------
    def _guardar_movimiento(self, producto, tipo, cantidad, precio, motivo):
        """
        Actualiza el stock y registra el movimiento en una sola transacción.
        El stock se calcula en la base de datos (no con el valor que tenía
        el formulario), así dos usuarios a la vez no se pisan.
        Devuelve el nuevo stock, o None si no se pudo registrar.
        """

        conexion = self._conectar_o_avisar()

        if conexion is None:
            return None

        try:
            cursor = conexion.cursor()

            if tipo == "Entrada":
                cursor.execute(
                    """
                    UPDATE productos
                    SET stock_actual = stock_actual + %s
                    WHERE id_producto = %s
                    """,
                    (cantidad, producto["id"])
                )
            else:
                cursor.execute(
                    """
                    UPDATE productos
                    SET stock_actual = stock_actual - %s
                    WHERE id_producto = %s
                    AND stock_actual >= %s
                    """,
                    (cantidad, producto["id"], cantidad)
                )

                if cursor.rowcount == 0:
                    conexion.rollback()
                    cursor.close()

                    QMessageBox.warning(
                        self,
                        "Stock insuficiente",
                        "El stock disponible cambió. "
                        "No se pudo registrar la salida."
                    )
                    return None

            cursor.execute(
                """
                SELECT stock_actual
                FROM productos
                WHERE id_producto = %s
                """,
                (producto["id"],)
            )

            nuevo_stock = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO movimientos
                (
                    id_producto,
                    tipo,
                    cantidad,
                    precio_unitario,
                    fecha,
                    motivo,
                    stock_resultante
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    producto["id"],
                    tipo,
                    cantidad,
                    precio,
                    QDate.currentDate().toString("yyyy-MM-dd"),
                    motivo,
                    nuevo_stock,
                )
            )

            conexion.commit()
            cursor.close()

            return nuevo_stock

        except Exception as e:
            conexion.rollback()

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo registrar la {tipo.lower()}:\n{e}"
            )
            return None

        finally:
            self.db.cerrar()

    def _registrar(self, tipo, clase_formulario):

        # Evita abrir dos formularios si el usuario hace clic varias veces
        if self._abriendo_formulario:
            return

        self._abriendo_formulario = True

        # Se leen los productos más recientes (en un hilo) y recién entonces
        # se abre el formulario
        self.cargar_productos(
            lambda: self._abrir_formulario(tipo, clase_formulario)
        )

    def _abrir_formulario(self, tipo, clase_formulario):

        self._abriendo_formulario = False

        if not self.productos:
            QMessageBox.warning(
                self,
                "Sin productos",
                "Debe existir al menos un producto."
            )
            return

        dialogo = clase_formulario(self.productos, self)

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        datos = dialogo.datos
        producto = datos["producto"]
        cantidad = datos["cantidad"]
        precio = datos["precio"]

        nuevo_stock = self._guardar_movimiento(
            producto, tipo, cantidad, precio, datos["motivo"]
        )

        if nuevo_stock is None:
            return

        def avisar():
            # Se emite cuando el historial ya está actualizado
            if self.movimientos:
                self.movimiento_registrado.emit(self.movimientos[0])

        self.cargar_productos()
        self.cargar_movimientos(avisar)

        if tipo == "Entrada":
            titulo = "Entrada registrada"
            texto = "una entrada"
            etiqueta_precio = "Precio de compra"
        else:
            titulo = "Salida registrada"
            texto = "una salida"
            etiqueta_precio = "Precio de venta"

        QMessageBox.information(
            self,
            titulo,
            f'Se registró {texto} de {cantidad} '
            f'unidades de "{producto["nombre"]}".\n\n'
            f'{etiqueta_precio}: C$ {precio:.2f}\n'
            f'Nuevo stock: {nuevo_stock}'
        )

    def registrar_entrada(self):
        self._registrar("Entrada", FormularioEntrada)

    def registrar_salida(self):
        self._registrar("Salida", FormularioSalida)

    # ------------------------------------------------------------------
    # Filtros
    # ------------------------------------------------------------------
    def movimiento_en_rango(self, fecha_movimiento, filtro):

        fecha = QDate.fromString(fecha_movimiento, "dd-MM-yyyy")
        hoy = QDate.currentDate()

        if not fecha.isValid():
            return False

        if filtro == "Todas las fechas":
            return True

        if filtro == "Hoy":
            return fecha == hoy

        if filtro == "Ayer":
            return fecha == hoy.addDays(-1)

        if filtro == "Últimos 7 días":
            return hoy.addDays(-6) <= fecha <= hoy

        if filtro == "Este mes":
            return (
                fecha.year() == hoy.year()
                and fecha.month() == hoy.month()
            )

        if filtro == "Mes pasado":
            mes_anterior = hoy.addMonths(-1)
            return (
                fecha.year() == mes_anterior.year()
                and fecha.month() == mes_anterior.month()
            )

        return True

    def aplicar_filtros(self, *_):

        texto = self.buscar.text().lower().strip()
        filtro_fecha = self.fecha.currentText()

        for fila in range(self.tabla.rowCount()):

            fecha_item = self.tabla.item(fila, 0)

            if not fecha_item:
                continue

            # Producto, tipo, usuario y motivo
            texto_movimiento = " ".join(
                self.tabla.item(fila, columna).text().lower()
                for columna in (1, 2, 6, 7)
                if self.tabla.item(fila, columna)
            )

            mostrar = (
                texto in texto_movimiento
                and self.movimiento_en_rango(
                    fecha_item.text(), filtro_fecha
                )
            )

            self.tabla.setRowHidden(fila, not mostrar)


if __name__ == "__main__":

    app = QApplication(sys.argv)

    ventana = Movimientos()
    ventana.show()

    sys.exit(app.exec())