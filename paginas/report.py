import sys
from html import escape

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QFrame,
    QDialog,
    QApplication,
    QGroupBox,
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
    QMessageBox,
    QDialogButtonBox,
    QScrollArea,
    QFileDialog,
)
from PySide6.QtCore import Qt, Signal, Slot, QDate
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument
from hilo.hilo import consultar, Cargador
from estilos.estilos import (
    ESTILO_PRODUCTOS,
    ESTILO_TITULO,
    ESTILO_SUBTITULO,
    ESTILO_INDICADOR_REPORTE,
    ESTILO_INDICADOR_TITULO_REPORTE,
    ESTILO_INDICADOR_VALOR_REPORTE,
    ESTILO_INDICADOR_DESCRIPCION_REPORTE,
    ESTILO_DIALOGO_REPORTE,
    ESTILO_GRUPO_REPORTE,
    ESTILO_BOTONES_PAGINA_REPORTE,
)

TODAS_CATEGORIAS = "Todas las categorías"

SQL_CATEGORIAS = """
    SELECT nombre
    FROM categorias
    WHERE estado = 'Activo'
    ORDER BY nombre
"""

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
        p.codigo,
        p.nombre AS producto,
        m.tipo,
        m.cantidad,
        m.precio_unitario AS precio,
        m.fecha,
        m.motivo,
        m.stock_resultante
    FROM movimientos m
    INNER JOIN productos p
        ON m.id_producto = p.id_producto
    ORDER BY m.id_movimiento
"""

ESTILO_VENTANA_REPORTE = """
    QMainWindow, QWidget {
        background-color: #FFFFFF;
        color: #263238;
    }

    QComboBox {
        background-color: #FFFFFF;
        color: #263238;
        border: 1px solid #DCE3EA;
        border-radius: 6px;
        padding: 6px 10px;
        min-height: 24px;
    }

    QComboBox::drop-down {
        background-color: #FFFFFF;
        border: none;
        width: 28px;
    }

    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        color: #263238;
        border: 1px solid #DCE3EA;
        selection-background-color: #D9EEF9;
        selection-color: #263238;
        outline: none;
    }

    QLineEdit {
        background-color: #FFFFFF;
        color: #263238;
        border: 1px solid #DCE3EA;
        border-radius: 6px;
        padding: 6px 8px;
    }

    QLineEdit:focus {
        border: 1px solid #3498DB;
    }

    QScrollArea, QScrollArea > QWidget > QWidget {
        background-color: #FFFFFF;
        border: none;
    }
"""


class GenerarReporteDialog(QDialog):

    def __init__(self, reporte, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Reporte de Inventario")
        self.setModal(True)
        self.resize(450, 350)
        self.setStyleSheet(ESTILO_DIALOGO_REPORTE)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(15)

        titulo = QLabel("Resumen del reporte")
        titulo.setStyleSheet(ESTILO_TITULO)
        layout_principal.addWidget(titulo)

        grupo = QGroupBox("Información del reporte")
        grupo.setStyleSheet(ESTILO_GRUPO_REPORTE)

        formulario = QFormLayout()
        formulario.setSpacing(12)

        formulario.addRow("Fecha:", QLabel(reporte["fecha"]))
        formulario.addRow("Categoría:", QLabel(reporte["categoria"]))
        formulario.addRow("Productos:", QLabel(str(reporte["productos"])))
        formulario.addRow("Entradas:", QLabel(str(reporte["entradas"])))
        formulario.addRow("Salidas:", QLabel(str(reporte["salidas"])))
        formulario.addRow(
            "Venta Total:",
            QLabel(f'C$ {reporte["venta_total"]:.2f}')
        )

        grupo.setLayout(formulario)
        layout_principal.addWidget(grupo)

        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        botones.setStyleSheet(ESTILO_BOTONES_PAGINA_REPORTE)
        botones.accepted.connect(self.accept)

        layout_principal.addWidget(botones)


class Indicador(QFrame):

    def __init__(self, titulo, valor, descripcion):
        super().__init__()

        self.titulo = QLabel(titulo)
        self.valor = QLabel(valor)
        self.descripcion = QLabel(descripcion)

        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.descripcion.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setStyleSheet(ESTILO_INDICADOR_REPORTE)
        self.titulo.setStyleSheet(ESTILO_INDICADOR_TITULO_REPORTE)
        self.valor.setStyleSheet(ESTILO_INDICADOR_VALOR_REPORTE)
        self.descripcion.setStyleSheet(ESTILO_INDICADOR_DESCRIPCION_REPORTE)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(5)

        layout.addWidget(self.titulo)
        layout.addWidget(self.valor)
        layout.addWidget(self.descripcion)

        self.setLayout(layout)

        self.setMinimumHeight(140)
        self.setMaximumHeight(160)


class Reporte(QMainWindow):

    datos = Signal()

    def __init__(self, productos=None, movimientos=None):
        super().__init__()

        self.setWindowTitle("Reportes")
        self.resize(1000, 650)
        self.setStyleSheet(ESTILO_PRODUCTOS + ESTILO_VENTANA_REPORTE)

        self.productos = []
        self.movimientos = []

        self._cargador_categorias = Cargador()
        self._cargador_datos = Cargador()

        widget = QWidget()
        self.setCentralWidget(widget)

        layout_exterior = QVBoxLayout(widget)
        layout_exterior.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        contenido = QWidget()
        scroll.setWidget(contenido)

        layout_principal = QVBoxLayout(contenido)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(15)

        titulo = QLabel("Reportes")
        subtitulo = QLabel("Información general del inventario")

        titulo.setStyleSheet(ESTILO_TITULO)
        subtitulo.setStyleSheet(ESTILO_SUBTITULO)

        layout_principal.addWidget(titulo)
        layout_principal.addWidget(subtitulo)

        # ---------- Filtros ----------
        layout_buscar = QHBoxLayout()

        self.reporte = QComboBox()
        self.reporte.addItem(TODAS_CATEGORIAS)
        self.cargar_categorias()
        # Al cambiar la categoría solo se recalcula con los datos ya cargados
        self.reporte.currentTextChanged.connect(
            lambda _texto: self._refrescar()
        )

        self.fecha = QLineEdit()
        self.fecha.setPlaceholderText("DD-MM-AAAA")

        self.fecha2 = QLineEdit()
        self.fecha2.setPlaceholderText("DD-MM-AAAA")

        self.btn_generar = QPushButton("Generar Reporte")
        self.btn_generar.setStyleSheet(ESTILO_BOTONES_PAGINA_REPORTE)
        self.btn_generar.clicked.connect(self.generar_reporte)

        layout_buscar.addWidget(self.reporte)
        layout_buscar.addWidget(QLabel("Desde:"))
        layout_buscar.addWidget(self.fecha)
        layout_buscar.addWidget(QLabel("Hasta:"))
        layout_buscar.addWidget(self.fecha2)
        layout_buscar.addWidget(self.btn_generar)

        layout_principal.addLayout(layout_buscar)

        # ---------- Indicadores ----------
        layout_indicadores = QHBoxLayout()
        layout_indicadores.setSpacing(15)

        self.indicador_productos = Indicador(
            "Productos", "0", "Total de productos"
        )
        self.indicador_alerta = Indicador(
            "Stock Bajo", "0", "Productos con stock bajo"
        )
        self.indicador_entradas = Indicador(
            "Entradas", "0", "Total de entradas"
        )
        self.indicador_salidas = Indicador(
            "Salidas", "0", "Total de salidas"
        )
        self.indicador_venta_total = Indicador(
            "Venta Total", "0", "Total de ventas"
        )

        for indicador in (
            self.indicador_productos,
            self.indicador_alerta,
            self.indicador_entradas,
            self.indicador_salidas,
            self.indicador_venta_total,
        ):
            layout_indicadores.addWidget(indicador)

        layout_principal.addLayout(layout_indicadores)

        # ---------- Tabla ----------
        label = QLabel("Reporte de Inventario")
        label.setStyleSheet(ESTILO_TITULO)
        layout_principal.addWidget(label)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "Producto",
            "Categoría",
            "Stock",
            "Entradas",
            "Salidas",
            "Precio",
            "Venta",
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
        self.tabla.setMinimumHeight(300)

        layout_principal.addWidget(self.tabla)

        # ---------- Botones ----------
        layout_botones = QHBoxLayout()

        self.btn_exportar = QPushButton("Exportar a PDF")
        self.btn_exportar.setStyleSheet(ESTILO_BOTONES_PAGINA_REPORTE)
        self.btn_exportar.clicked.connect(self.exportar_pdf)

        self.btn_imprimir = QPushButton("Imprimir Reporte")
        self.btn_imprimir.setStyleSheet(ESTILO_BOTONES_PAGINA_REPORTE)
        self.btn_imprimir.clicked.connect(self.imprimir_reporte)

        layout_botones.addWidget(self.btn_exportar)
        layout_botones.addWidget(self.btn_imprimir)

        layout_principal.addLayout(layout_botones)

        layout_exterior.addWidget(scroll)

        self.actualizar_reporte()

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------
    def cargar_categorias(self):
        """Lee las categorías en un hilo y llena el combo al terminar."""

        self._cargador_categorias.cargar(
            lambda: consultar(SQL_CATEGORIAS),
            self._categorias_listas,
            self._error_carga,
        )

    def _categorias_listas(self, categorias):

        seleccion_previa = self.reporte.currentText()

        self.reporte.blockSignals(True)

        self.reporte.clear()
        self.reporte.addItem(TODAS_CATEGORIAS)

        for categoria in categorias:
            self.reporte.addItem(categoria["nombre"])

        # Conserva la categoría elegida si todavía existe
        indice = self.reporte.findText(seleccion_previa)
        self.reporte.setCurrentIndex(indice if indice >= 0 else 0)

        self.reporte.blockSignals(False)

        # Si la categoría elegida desapareció, se recalcula el reporte
        if self.reporte.currentText() != seleccion_previa and self.productos:
            self._refrescar()

    def cargar_datos(self, al_terminar=None):
        """
        Lee productos y movimientos en un hilo. `al_terminar` se ejecuta
        cuando los datos ya están disponibles en self.productos / movimientos.
        """

        self._cargador_datos.cargar(
            lambda: (consultar(SQL_PRODUCTOS), consultar(SQL_MOVIMIENTOS)),
            lambda datos: self._datos_listos(datos, al_terminar),
            self._error_carga,
        )

    def _datos_listos(self, datos, al_terminar=None):

        self.productos, self.movimientos = datos

        if al_terminar is not None:
            al_terminar()

    def _error_carga(self, mensaje):

        print(f"Error al cargar datos para reportes: {mensaje}")


    # ------------------------------------------------------------------
    # Fechas
    # ------------------------------------------------------------------
    @staticmethod
    def _leer_fecha(texto):
        """None = vacío, False = inválida, QDate = válida."""

        texto = texto.strip()

        if not texto:
            return None

        fecha = QDate.fromString(texto, "dd-MM-yyyy")

        return fecha if fecha.isValid() else False

    def obtener_fecha_desde(self):
        return self._leer_fecha(self.fecha.text())

    def obtener_fecha_hasta(self):
        return self._leer_fecha(self.fecha2.text())

    def validar_fechas(self):

        fecha_desde = self.obtener_fecha_desde()
        fecha_hasta = self.obtener_fecha_hasta()

        if fecha_desde is False:
            QMessageBox.warning(
                self,
                "Fecha incorrecta",
                "La fecha Desde debe tener el formato DD-MM-AAAA."
            )
            return None

        if fecha_hasta is False:
            QMessageBox.warning(
                self,
                "Fecha incorrecta",
                "La fecha Hasta debe tener el formato DD-MM-AAAA."
            )
            return None

        if (
            fecha_desde is not None
            and fecha_hasta is not None
            and fecha_desde > fecha_hasta
        ):
            QMessageBox.warning(
                self,
                "Rango incorrecto",
                "La fecha Desde no puede ser mayor que la fecha Hasta."
            )
            return None

        return fecha_desde, fecha_hasta

    def texto_rango(self):

        desde = self.fecha.text().strip()
        hasta = self.fecha2.text().strip()

        if desde and hasta:
            return f"{desde} al {hasta}"
        if desde:
            return f"Desde {desde}"
        if hasta:
            return f"Hasta {hasta}"
        return "Todas las fechas"

    # ------------------------------------------------------------------
    # Cálculo del reporte
    # ------------------------------------------------------------------
    def obtener_datos_reporte(self):

        fechas = self.validar_fechas()

        if fechas is None:
            return None

        fecha_desde, fecha_hasta = fechas
        categoria_seleccionada = self.reporte.currentText()

        # Trabaja con los datos ya cargados (self.productos / self.movimientos)

        # Movimientos filtrados por fecha, agrupados por código de producto
        movimientos_por_codigo = {}

        for movimiento in self.movimientos:

            fecha = movimiento["fecha"]

            if hasattr(fecha, "year"):
                fecha_movimiento = QDate(fecha.year, fecha.month, fecha.day)
            else:
                fecha_movimiento = QDate.fromString(
                    str(fecha)[:10], "yyyy-MM-dd"
                )

            if not fecha_movimiento.isValid():
                continue

            if fecha_desde is not None and fecha_movimiento < fecha_desde:
                continue

            if fecha_hasta is not None and fecha_movimiento > fecha_hasta:
                continue

            movimientos_por_codigo.setdefault(
                movimiento.get("codigo"), []
            ).append(movimiento)

        datos = []

        for producto in self.productos:

            categoria = producto.get("categoria", "")

            if (
                categoria_seleccionada != TODAS_CATEGORIAS
                and categoria != categoria_seleccionada
            ):
                continue

            entradas = 0
            salidas = 0
            venta_total = 0

            for movimiento in movimientos_por_codigo.get(
                producto.get("codigo"), []
            ):
                tipo = movimiento.get("tipo")

                if tipo == "Entrada":
                    entradas += 1

                elif tipo == "Salida":
                    salidas += 1

                    cantidad = movimiento.get("cantidad") or 0
                    precio = movimiento.get("precio")

                    if precio is None:
                        precio = producto.get("precio") or 0

                    venta_total += cantidad * precio

            datos.append({
                "producto": producto.get("nombre", ""),
                "categoria": categoria,
                "stock": producto.get("stock", 0),
                "stock_minimo": producto.get("stock_minimo", 0),
                "entradas": entradas,
                "salidas": salidas,
                "precio": producto.get("precio", 0),
                "venta": venta_total,
            })

        return datos

    @staticmethod
    def calcular_totales(datos):

        return {
            "productos": len(datos),
            "stock_bajo": sum(
                1 for r in datos if r["stock"] <= r["stock_minimo"]
            ),
            "entradas": sum(r["entradas"] for r in datos),
            "salidas": sum(r["salidas"] for r in datos),
            "venta_total": sum(r["venta"] for r in datos),
        }

    # ------------------------------------------------------------------
    # Actualización de la interfaz
    # ------------------------------------------------------------------
    def _refrescar(self):
        """Recalcula el reporte, actualiza tabla e indicadores y devuelve los datos."""

        datos = self.obtener_datos_reporte()

        if datos is None:
            return None

        self.tabla.setRowCount(0)

        for registro in datos:

            fila = self.tabla.rowCount()
            self.tabla.insertRow(fila)

            valores = [
                registro["producto"],
                registro["categoria"],
                str(registro["stock"]),
                str(registro["entradas"]),
                str(registro["salidas"]),
                f'C$ {registro["precio"]:.2f}',
                f'C$ {registro["venta"]:.2f}',
            ]

            for columna, valor in enumerate(valores):
                self.tabla.setItem(fila, columna, QTableWidgetItem(valor))

        totales = self.calcular_totales(datos)

        self.indicador_productos.valor.setText(str(totales["productos"]))
        self.indicador_alerta.valor.setText(str(totales["stock_bajo"]))
        self.indicador_entradas.valor.setText(str(totales["entradas"]))
        self.indicador_salidas.valor.setText(str(totales["salidas"]))
        self.indicador_venta_total.valor.setText(
            f'C$ {totales["venta_total"]:.2f}'
        )

        return datos

    @Slot()
    def actualizar_reporte(self):
        """Vuelve a leer la base de datos (en un hilo) y recalcula el reporte."""

        self.cargar_datos(self._refrescar)

    @Slot(dict)
    def recibir_movimiento(self, movimiento):
        self.actualizar_reporte()

    @Slot()
    def aplicar_filtros(self):
        self._refrescar()

    @Slot()
    def actualizar_categorias(self):
        self.cargar_categorias()
        self.actualizar_reporte()

    @Slot()
    def generar_reporte(self):

        # Valida las fechas antes de consultar la base de datos
        if self.validar_fechas() is None:
            return

        self.cargar_datos(self._mostrar_resumen)

    def _mostrar_resumen(self):

        datos = self._refrescar()

        if datos is None:
            return

        totales = self.calcular_totales(datos)

        resumen = {
            "fecha": self.texto_rango(),
            "categoria": self.reporte.currentText(),
            "productos": totales["productos"],
            "entradas": totales["entradas"],
            "salidas": totales["salidas"],
            "venta_total": totales["venta_total"],
        }

        GenerarReporteDialog(resumen, self).exec()

    # ------------------------------------------------------------------
    # HTML / PDF / Impresión
    # ------------------------------------------------------------------
    def generar_html(self):

        datos = self.obtener_datos_reporte()

        if datos is None:
            return None

        categoria = escape(self.reporte.currentText())
        rango = escape(self.texto_rango())
        totales = self.calcular_totales(datos)

        filas = ""

        # QTextDocument no soporta tr:nth-child, por eso se alterna el color a mano
        for i, registro in enumerate(datos):

            fondo = "#F5F7FA" if i % 2 else "#FFFFFF"

            filas += f"""
            <tr bgcolor="{fondo}">
                <td>{escape(str(registro["producto"]))}</td>
                <td>{escape(str(registro["categoria"]))}</td>
                <td>{registro["stock"]}</td>
                <td>{registro["entradas"]}</td>
                <td>{registro["salidas"]}</td>
                <td>C$ {registro["precio"]:.2f}</td>
                <td>C$ {registro["venta"]:.2f}</td>
            </tr>
            """

        html = f"""
        <html>
        <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial; font-size: 11pt; }}
            h1 {{ text-align: center; }}
            h2 {{ margin-top: 25px; }}
            p {{ font-size: 10pt; }}
            th {{
                background-color: #3498DB;
                color: white;
                padding: 8px;
            }}
            td {{ padding: 7px; }}
        </style>
        </head>

        <body>

        <h1>Reporte de Inventario</h1>

        <p><b>Categoría:</b> {categoria}</p>
        <p><b>Período:</b> {rango}</p>

        <p><b>Total de productos:</b> {totales["productos"]}</p>
        <p><b>Productos con stock bajo:</b> {totales["stock_bajo"]}</p>
        <p><b>Total de entradas:</b> {totales["entradas"]}</p>
        <p><b>Total de salidas:</b> {totales["salidas"]}</p>
        <p><b>Venta total:</b> C$ {totales["venta_total"]:.2f}</p>

        <h2>Inventario</h2>

        <table width="100%" border="1" cellspacing="0" cellpadding="6">
        <tr>
            <th>Producto</th>
            <th>Categoría</th>
            <th>Stock</th>
            <th>Entradas</th>
            <th>Salidas</th>
            <th>Precio</th>
            <th>Venta</th>
        </tr>

        {filas}

        </table>

        </body>
        </html>
        """

        return html

    @Slot()
    def exportar_pdf(self):

        html = self.generar_html()

        if html is None:
            return

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte",
            "reporte_inventario.pdf",
            "Archivos PDF (*.pdf)"
        )

        if not ruta:
            return

        if not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(ruta)

        documento = QTextDocument()
        documento.setHtml(html)
        documento.print_(printer)

        QMessageBox.information(
            self,
            "Reporte generado",
            "El reporte PDF se generó correctamente."
        )

    @Slot()
    def imprimir_reporte(self):

        html = self.generar_html()

        if html is None:
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialogo = QPrintDialog(printer, self)

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        documento = QTextDocument()
        documento.setHtml(html)
        documento.print_(printer)

        QMessageBox.information(
            self,
            "Impresión",
            "El reporte fue enviado a la impresora."
        )


if __name__ == "__main__":

    app = QApplication(sys.argv)

    ventana = Reporte()
    ventana.show()

    sys.exit(app.exec())