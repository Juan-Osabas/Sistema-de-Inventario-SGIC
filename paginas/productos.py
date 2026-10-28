import sys

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QTableWidgetItem,
    QHeaderView,
    QMainWindow,
    QTableWidget,
    QHBoxLayout,
    QApplication,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QWidget,
    QDialog,
    QFormLayout,
    QDoubleSpinBox,
    QSpinBox,
    QMessageBox,
    QDialogButtonBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from paginas.conexion import ConexionMySQL
from hilo.hilo import consultar, Cargador
from estilos.estilos import ESTILO_PRODUCTOS, ESTILO_EDITAR, ESTILO_ELIMINAR

TODAS_CATEGORIAS = "Todas las categorías"

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
    ORDER BY p.id_producto
"""


class FormularioProducto(QDialog):

    def __init__(self, categorias, producto=None, parent=None):

        super().__init__(parent)

        self.producto = producto
        self.datos_producto = None

        self.setWindowTitle(
            "Agregar Producto" if producto is None else "Editar Producto"
        )
        self.setModal(True)
        self.resize(450, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        titulo = QLabel(
            "Nuevo producto" if producto is None else "Editar producto"
        )
        titulo.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
        """)
        layout.addWidget(titulo)

        formulario = QFormLayout()
        formulario.setSpacing(12)

        self.codigo = QLineEdit()
        self.codigo.setPlaceholderText("Ej. 001")
        formulario.addRow("Código:", self.codigo)

        self.nombre = QLineEdit()
        self.nombre.setPlaceholderText("Nombre del producto")
        formulario.addRow("Nombre:", self.nombre)

        self.descripcion = QLineEdit()
        self.descripcion.setPlaceholderText("Descripción del producto")
        formulario.addRow("Descripción:", self.descripcion)

        self.categoria = QComboBox()
        self.categoria.addItems(categorias)
        formulario.addRow("Categoría:", self.categoria)

        self.precio = QDoubleSpinBox()
        self.precio.setRange(0, 9999999.99)
        self.precio.setDecimals(2)
        self.precio.setPrefix("C$ ")
        formulario.addRow("Precio:", self.precio)

        self.stock = QSpinBox()
        self.stock.setRange(0, 9999999)
        formulario.addRow(
            "Stock inicial:" if producto is None else "Stock actual:",
            self.stock
        )

        self.stock_minimo = QSpinBox()
        self.stock_minimo.setRange(0, 9999999)
        formulario.addRow("Stock mínimo:", self.stock_minimo)

        layout.addLayout(formulario)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        botones.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")

        botones.accepted.connect(self.guardar)
        botones.rejected.connect(self.reject)

        layout.addWidget(botones)

        if producto is not None:

            self.codigo.setText(str(producto["codigo"] or ""))
            self.nombre.setText(producto["nombre"] or "")
            self.descripcion.setText(producto["descripcion"] or "")

            indice = self.categoria.findText(producto["categoria"])

            if indice >= 0:
                self.categoria.setCurrentIndex(indice)

            # float(): QDoubleSpinBox no acepta Decimal (lo que devuelve MySQL)
            self.precio.setValue(float(producto["precio"] or 0))
            self.stock.setValue(int(producto["stock"] or 0))
            self.stock_minimo.setValue(int(producto["stock_minimo"] or 0))

    def guardar(self):

        datos_producto = {
            "codigo": self.codigo.text().strip(),
            "nombre": self.nombre.text().strip(),
            "descripcion": self.descripcion.text().strip(),
            "categoria": self.categoria.currentText(),
            "precio": self.precio.value(),
            "stock": self.stock.value(),
            "stock_minimo": self.stock_minimo.value(),
        }

        if not datos_producto["codigo"]:
            QMessageBox.warning(
                self,
                "Dato requerido",
                "Debe ingresar el código del producto."
            )
            self.codigo.setFocus()
            return

        if not datos_producto["nombre"]:
            QMessageBox.warning(
                self,
                "Dato requerido",
                "Debe ingresar el nombre del producto."
            )
            self.nombre.setFocus()
            return

        if not datos_producto["categoria"]:
            QMessageBox.warning(
                self,
                "Dato requerido",
                "Debe seleccionar una categoría."
            )
            return

        if datos_producto["precio"] <= 0:
            QMessageBox.warning(
                self,
                "Precio inválido",
                "El precio debe ser mayor que cero."
            )
            self.precio.setFocus()
            return

        self.datos_producto = datos_producto

        self.accept()


class Producto(QMainWindow):

    stocks = Signal(dict)
    producto_guardado = Signal(dict)
    producto_eliminado = Signal(dict)
    categorias_cambiadas = Signal(list)
    regresar_inicio = Signal()
    productos_cargados = Signal()

    def __init__(self, categorias=None):

        super().__init__()
        self.setStyleSheet(ESTILO_PRODUCTOS)

        self.setWindowTitle("Productos")
        self.resize(1000, 650)

        self.categorias = categorias if categorias is not None else []

        self.db = ConexionMySQL()

        self.productos = []
        self._cargador = Cargador()

        widget = QWidget()
        self.setCentralWidget(widget)

        layout_principal = QVBoxLayout(widget)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(15)

        layout_encabezado = QVBoxLayout()

        titulo = QLabel("Productos")
        subtitulo = QLabel("Gestión y consulta de productos de inventario")

        titulo.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
        """)
        subtitulo.setStyleSheet("""
            font-size: 14px;
        """)

        layout_encabezado.addWidget(titulo)
        layout_encabezado.addWidget(subtitulo)

        layout_principal.addLayout(layout_encabezado)

        layout_buscar = QHBoxLayout()

        label_buscar = QLabel("Buscar Producto:")

        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("Buscar por código o nombre...")
        self.buscar.setClearButtonEnabled(True)
        self.buscar.textChanged.connect(self.filtrar_tabla)

        self.filtro_categoria = QComboBox()
        self.actualizar_categorias()
        self.filtro_categoria.currentTextChanged.connect(self.filtrar_tabla)

        btn_agregar = QPushButton("Agregar Producto")
        btn_agregar.clicked.connect(self.agregar_producto)

        layout_buscar.addWidget(label_buscar)
        layout_buscar.addWidget(self.buscar)
        layout_buscar.addWidget(self.filtro_categoria)
        layout_buscar.addWidget(btn_agregar)

        layout_principal.addLayout(layout_buscar)

        self.tabla_productos = QTableWidget()
        self.tabla_productos.setColumnCount(7)
        self.tabla_productos.setHorizontalHeaderLabels([
            "Código",
            "Producto",
            "Categoría",
            "Precio",
            "Stock",
            "Stock min",
            "Acciones",
        ])
        self.tabla_productos.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabla_productos.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tabla_productos.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tabla_productos.verticalHeader().setVisible(False)

        # Filas más altas y columna de acciones con ancho fijo para que
        # los botones Editar / Eliminar no se corten
        self.tabla_productos.verticalHeader().setDefaultSectionSize(48)
        self.tabla_productos.horizontalHeader().setSectionResizeMode(
            6, QHeaderView.ResizeMode.Fixed
        )
        self.tabla_productos.setColumnWidth(6, 220)

        layout_principal.addWidget(self.tabla_productos)

        self.cargar_productos()

    # ------------------------------------------------------------------
    # Auxiliares
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

    @staticmethod
    def _existe(cursor, campo, valor, excluir_id=None):
        """Comprueba si ya existe un producto con ese nombre o código."""

        if campo == "nombre":
            condicion = "LOWER(nombre) = LOWER(%s)"
        else:
            condicion = "codigo = %s"

        sql = f"SELECT id_producto FROM productos WHERE {condicion}"
        params = [valor]

        if excluir_id is not None:
            sql += " AND id_producto != %s"
            params.append(excluir_id)

        cursor.execute(sql, tuple(params))

        return cursor.fetchone() is not None

    def _producto_por_id(self, id_producto):

        return next(
            (p for p in self.productos if p["id"] == id_producto),
            None
        )

    def _emitir_cambio(self, producto):

        # Evita emitir None, que rompería las señales de tipo dict
        if producto is None:
            return

        self.producto_guardado.emit(producto)
        self.stocks.emit(producto)

    def obtener_nombres_categorias(self):

        if not self.categorias:
            return []

        if isinstance(self.categorias[0], dict):
            return [
                categoria["nombre"]
                for categoria in self.categorias
                if categoria["estado"] == "Activo"
            ]

        return list(self.categorias)

    def actualizar_categorias(self, categorias=None, recargar=True):

        if categorias is not None:
            self.categorias = categorias

        nombres = self.obtener_nombres_categorias()

        categoria_actual = (
            self.filtro_categoria.currentText()
            if self.filtro_categoria.count() > 0
            else TODAS_CATEGORIAS
        )

        self.filtro_categoria.blockSignals(True)

        self.filtro_categoria.clear()
        self.filtro_categoria.addItem(TODAS_CATEGORIAS)
        self.filtro_categoria.addItems(nombres)

        indice = self.filtro_categoria.findText(categoria_actual)

        if indice >= 0:
            self.filtro_categoria.setCurrentIndex(indice)

        self.filtro_categoria.blockSignals(False)

        self.categorias_cambiadas.emit(nombres)

        # Durante __init__ la tabla todavía no existe.
        # recargar=False: solo llegó la lista de categorías (primera carga),
        # no hace falta volver a consultar los productos.
        if hasattr(self, "tabla_productos"):

            if recargar:
                self.cargar_productos()
            else:
                self.filtrar_tabla()

    # ------------------------------------------------------------------
    # Tabla
    # ------------------------------------------------------------------
    def actualizar_tabla(self):

        self.tabla_productos.setRowCount(0)

        for producto in self.productos:

            fila = self.tabla_productos.rowCount()
            self.tabla_productos.insertRow(fila)

            stock = producto["stock"] or 0
            stock_minimo = producto["stock_minimo"] or 0

            valores = [
                str(producto["codigo"] or ""),
                producto["nombre"] or "",
                producto["categoria"] or "",
                f'C$ {producto["precio"]:.2f}',
                str(stock),
                str(stock_minimo),
            ]

            for columna, valor in enumerate(valores):

                item = QTableWidgetItem(valor)

                if columna in (4, 5):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Stock en rojo cuando está en el mínimo o por debajo
                if columna == 4 and stock <= stock_minimo:
                    item.setForeground(QColor("#C0392B"))

                self.tabla_productos.setItem(fila, columna, item)

            contenedor = QWidget()

            layout_acciones = QHBoxLayout(contenedor)
            layout_acciones.setContentsMargins(5, 2, 5, 2)
            layout_acciones.setSpacing(5)

            btn_editar = QPushButton("Editar")
            btn_eliminar = QPushButton("Eliminar")

            btn_editar.clicked.connect(
                lambda checked=False, p=producto: self.editar_producto(p)
            )
            btn_eliminar.clicked.connect(
                lambda checked=False, p=producto: self.eliminar_producto(p)
            )

            layout_acciones.addWidget(btn_editar)
            layout_acciones.addWidget(btn_eliminar)

            btn_editar.setStyleSheet(ESTILO_EDITAR)
            btn_eliminar.setStyleSheet(ESTILO_ELIMINAR)

            self.tabla_productos.setCellWidget(fila, 6, contenedor)

        self.filtrar_tabla()

    def filtrar_tabla(self, texto=None):

        texto = self.buscar.text().lower().strip()
        categoria = self.filtro_categoria.currentText()

        for fila in range(self.tabla_productos.rowCount()):

            codigo_item = self.tabla_productos.item(fila, 0)
            nombre_item = self.tabla_productos.item(fila, 1)
            categoria_item = self.tabla_productos.item(fila, 2)

            if not codigo_item or not nombre_item or not categoria_item:
                continue

            coincide_texto = (
                texto in codigo_item.text().lower()
                or texto in nombre_item.text().lower()
            )

            coincide_categoria = (
                categoria == TODAS_CATEGORIAS
                or categoria_item.text() == categoria
            )

            self.tabla_productos.setRowHidden(
                fila,
                not (coincide_texto and coincide_categoria)
            )

    # ------------------------------------------------------------------
    # Base de datos
    # ------------------------------------------------------------------
    def cargar_productos(self, al_terminar=None):
        """
        Lee los productos en un hilo (la ventana no se congela) y refresca
        la tabla al terminar. `al_terminar` es opcional y se ejecuta después
        de que los datos ya están cargados.
        """

        self._cargador.cargar(
            lambda: consultar(SQL_PRODUCTOS),
            lambda filas: self._productos_listos(filas, al_terminar),
            self._error_carga_productos,
        )

    def _productos_listos(self, productos, al_terminar=None):

        # MySQL devuelve Decimal; se pasa a float para usarlo en
        # formularios y formatos sin errores
        for producto in productos:
            producto["precio"] = float(producto["precio"] or 0)

        self.productos = productos

        self.actualizar_tabla()
        self.productos_cargados.emit()

        if al_terminar is not None:
            al_terminar()

    def _error_carga_productos(self, mensaje):

        QMessageBox.critical(
            self,
            "Error al cargar los productos",
            f"No se pudieron cargar los productos:\n{mensaje}"
        )

    def agregar_producto(self):

        categorias = self.obtener_nombres_categorias()

        if not categorias:
            QMessageBox.warning(
                self,
                "Sin categorías",
                "Debe existir al menos una categoría activa."
            )
            return

        dialogo = FormularioProducto(categorias, parent=self)

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        producto = dialogo.datos_producto

        conexion = self._conectar_o_avisar()

        if conexion is None:
            return

        try:
            cursor = conexion.cursor()

            if self._existe(cursor, "nombre", producto["nombre"]):
                cursor.close()
                QMessageBox.warning(
                    self,
                    "Producto duplicado",
                    "Ya existe un producto con ese nombre."
                )
                return

            if self._existe(cursor, "codigo", producto["codigo"]):
                cursor.close()
                QMessageBox.warning(
                    self,
                    "Código duplicado",
                    "Ya existe un producto con ese código."
                )
                return

            cursor.execute(
                """
                SELECT id_categoria
                FROM categorias
                WHERE nombre = %s
                AND estado = 'Activo'
                """,
                (producto["categoria"],)
            )

            categoria = cursor.fetchone()

            if not categoria:
                cursor.close()
                QMessageBox.warning(
                    self,
                    "Categoría no encontrada",
                    "La categoría seleccionada no existe o está inactiva."
                )
                return

            cursor.execute(
                """
                INSERT INTO productos
                (
                    codigo,
                    nombre,
                    descripcion,
                    precio,
                    stock_actual,
                    stock_minimo,
                    id_categoria,
                    estado
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    producto["codigo"],
                    producto["nombre"],
                    producto["descripcion"],
                    producto["precio"],
                    producto["stock"],
                    producto["stock_minimo"],
                    categoria[0],
                    "Activo",
                )
            )

            id_nuevo = cursor.lastrowid

            conexion.commit()
            cursor.close()

        except Exception as e:
            conexion.rollback()

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar el producto:\n{e}"
            )
            return

        finally:
            self.db.cerrar()

        # Todo lo de abajo ocurre solo si el guardado fue exitoso,
        # fuera de la transacción ya cerrada
        self.cargar_productos(
            lambda: self._emitir_cambio(self._producto_por_id(id_nuevo))
        )

        QMessageBox.information(
            self,
            "Producto agregado",
            "El producto se agregó correctamente."
        )

    def editar_producto(self, producto):

        categorias = self.obtener_nombres_categorias()

        # Si la categoría del producto está inactiva, igual se muestra
        if producto["categoria"] not in categorias:
            categorias.insert(0, producto["categoria"])

        dialogo = FormularioProducto(categorias, producto, self)

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        nuevos_datos = dialogo.datos_producto

        conexion = self._conectar_o_avisar()

        if conexion is None:
            return

        try:
            cursor = conexion.cursor()

            cursor.execute(
                """
                SELECT id_categoria
                FROM categorias
                WHERE nombre = %s
                """,
                (nuevos_datos["categoria"],)
            )

            categoria = cursor.fetchone()

            if not categoria:
                cursor.close()
                QMessageBox.warning(
                    self,
                    "Categoría no encontrada",
                    "La categoría seleccionada ya no existe."
                )
                return

            if self._existe(
                cursor, "nombre", nuevos_datos["nombre"], producto["id"]
            ):
                cursor.close()
                QMessageBox.warning(
                    self,
                    "Producto duplicado",
                    "Ya existe otro producto con ese nombre."
                )
                return

            if self._existe(
                cursor, "codigo", nuevos_datos["codigo"], producto["id"]
            ):
                cursor.close()
                QMessageBox.warning(
                    self,
                    "Código duplicado",
                    "Ya existe otro producto con ese código."
                )
                return

            campos = [
                "codigo = %s",
                "nombre = %s",
                "descripcion = %s",
                "precio = %s",
                "stock_minimo = %s",
                "id_categoria = %s",
                "estado = %s",
            ]

            params = [
                nuevos_datos["codigo"],
                nuevos_datos["nombre"],
                nuevos_datos["descripcion"],
                nuevos_datos["precio"],
                nuevos_datos["stock_minimo"],
                categoria[0],
                producto["estado"] or "Activo",  # conserva el estado actual
            ]

            # El stock solo se toca si el usuario lo cambió. Así no se pisa
            # el stock real con un valor viejo del formulario.
            if nuevos_datos["stock"] != (producto["stock"] or 0):
                campos.append("stock_actual = %s")
                params.append(nuevos_datos["stock"])

            params.append(producto["id"])

            cursor.execute(
                f"""
                UPDATE productos
                SET {", ".join(campos)}
                WHERE id_producto = %s
                """,
                tuple(params)
            )

            conexion.commit()
            cursor.close()

        except Exception as e:
            conexion.rollback()

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo actualizar el producto:\n{e}"
            )
            return

        finally:
            self.db.cerrar()

        self.cargar_productos(
            lambda: self._emitir_cambio(
                self._producto_por_id(producto["id"])
            )
        )

        QMessageBox.information(
            self,
            "Producto actualizado",
            "El producto se actualizó correctamente."
        )

    def eliminar_producto(self, producto):

        respuesta = QMessageBox.question(
            self,
            "Eliminar producto",
            f'¿Está seguro de eliminar "{producto["nombre"]}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta != QMessageBox.StandardButton.Yes:
            return

        conexion = self._conectar_o_avisar()

        if conexion is None:
            return

        try:
            cursor = conexion.cursor()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM movimientos
                WHERE id_producto = %s
                """,
                (producto["id"],)
            )

            if cursor.fetchone()[0] > 0:
                cursor.close()
                QMessageBox.warning(
                    self,
                    "No se puede eliminar",
                    "Este producto tiene movimientos registrados "
                    "y no puede eliminarse porque afectaría "
                    "el historial del inventario."
                )
                return

            cursor.execute(
                """
                DELETE FROM productos
                WHERE id_producto = %s
                """,
                (producto["id"],)
            )

            conexion.commit()
            cursor.close()

        except Exception as e:
            conexion.rollback()

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo eliminar el producto:\n{e}"
            )
            return

        finally:
            self.db.cerrar()

        def avisar():
            self.producto_eliminado.emit(producto)
            self.stocks.emit(producto)

        self.cargar_productos(avisar)

        QMessageBox.information(
            self,
            "Producto eliminado",
            "El producto se eliminó correctamente."
        )

    def actualizar_desde_movimiento(self, datos=None):

        self.cargar_productos()


if __name__ == "__main__":

    app = QApplication(sys.argv)

    ventana = Producto()
    ventana.show()

    sys.exit(app.exec())