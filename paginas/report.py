"""
Página de Reportes.

Calcula, por producto, cuántas entradas y salidas hubo y cuánto se vendió,
filtrando por categoría y por rango de fechas (formato DD-MM-AAAA). Muestra
los resultados en cinco indicadores y en una tabla, y permite generar un
resumen, exportar el reporte a PDF o imprimirlo (ambos usan el mismo HTML).
Los cálculos se hacen en Python con los datos que se leen en segundo plano.
"""


# `sys` se usa solo al ejecutar este archivo directamente (ver el final).
import sys
# `escape` convierte caracteres especiales para insertarlos de forma segura en HTML
from html import escape
 
# Widgets de PySide6 usados en la página y en el diálogo de resumen.
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
# Qt: alineaciones. Signal/Slot: señales. QDate: fechas.
from PySide6.QtCore import Qt, Signal, Slot, QDate
# Impresión: QPrinter genera el PDF o imprime; QPrintDialog es el diálogo de impresora
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
# QTextDocument convierte HTML en un documento imprimible
from PySide6.QtGui import QTextDocument
# consultar/Cargador: lectura de la base de datos en segundo plano
from hilo.hilo import consultar, Cargador
# Estilos, colores del reporte HTML, consultas SQL y columnas del reporte (se
# definen en estilos/estilos.py)
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
    ESTILO_VENTANA_REPORTE,
    ESTILOS_REPORTE,
    COLOR_FILA_PAR,
    COLOR_FILA_IMPAR,
    COLOR_FILA_STOCK_BAJO,
    COLOR_TEXTO_STOCK_BAJO,
    COLOR_FILA_TOTALES,
    TODAS_CATEGORIAS,
    SQL_CATEGORIAS,
    SQL_PRODUCTOS,
    SQL_MOVIMIENTOS,
    COLUMNAS_REPORTE
)
 

 
def _moneda(valor):
    """Da formato de dinero, por ejemplo: C$ 1,234.50"""

    return f"C$ {valor:,.2f}"
 
 
def _formatear_celda(clave, valor):
    """Formatea el valor de una celda del reporte HTML (dinero o texto escapado)."""

    if clave in ("precio", "venta"):
        return _moneda(valor)
    return escape(str(valor))
 
 
class GenerarReporteDialog(QDialog):
    """Diálogo con el resumen del reporte generado (solo informativo)."""

 
    def __init__(self, reporte, parent=None):
        """`reporte`: dict con la fecha, la categoría y los totales a mostrar."""

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
 
        # Grupo con los datos del resumen, una fila por dato
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
    """Tarjeta con una cifra del reporte (título, valor grande y descripción)."""

 
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
    """
    Página de reportes: filtros, indicadores, tabla y exportación a PDF / impresión.
    """

 
    # Señal declarada, pero este archivo no la emite
    datos = Signal()
 
    def __init__(self, productos=None, movimientos=None):
        """
        Crea la interfaz; los datos reales se cargan en segundo plano (los parámetros
        `productos` y `movimientos` no se usan).
        """

        super().__init__()
 
        self.setWindowTitle("Reportes")
        self.resize(1000, 650)
        self.setStyleSheet(ESTILO_PRODUCTOS + ESTILO_VENTANA_REPORTE)
 
        # Copias locales de los datos; se llenan cuando termina cada carga
        self.productos = []
        self.movimientos = []
 
        # Un cargador por tipo de consulta para que no se descarten entre sí
        self._cargador_categorias = Cargador()
        self._cargador_datos = Cargador()
 
        widget = QWidget()
        self.setCentralWidget(widget)
 
        # Toda la página va dentro de un área con scroll por si la ventana es pequeña
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
 
        # Rango de fechas opcional (se valida en `validar_fechas`)
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
 
        # Se agregan las cinco tarjetas en una sola fila
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
        """
        Callback (hilo principal): llena el combo de categorías conservando la selección.
        """

 
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
        """
        Callback (hilo principal): guarda productos y movimientos y ejecuta `al_terminar`.
        """

 
        self.productos, self.movimientos = datos
 
        if al_terminar is not None:
            al_terminar()
 
    def _error_carga(self, mensaje):
        """Solo imprime el error en consola (no interrumpe al usuario con un aviso)."""

 
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
        """Fecha del campo "Desde" (ver `_leer_fecha`)."""

        return self._leer_fecha(self.fecha.text())
 
    def obtener_fecha_hasta(self):
        """Fecha del campo "Hasta" (ver `_leer_fecha`)."""

        return self._leer_fecha(self.fecha2.text())
 
    def validar_fechas(self):
        """
        Valida formato y orden de las fechas. Devuelve (desde, hasta), o None si hay
        un error (que ya se le avisó al usuario).
        """

 
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
        """Texto que describe el período elegido (para el resumen y el reporte)."""

 
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
        """
        Calcula una fila por producto (entradas, salidas y venta) con los datos ya
        cargados, respetando la categoría y el rango de fechas. None si las fechas
        son inválidas.
        """

 
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
 
            # La fecha puede venir como objeto fecha o como texto
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
 
            # Se omiten los productos de otras categorías
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
 
                # Entradas y salidas se cuentan por número de movimientos (no por unidades)
                if tipo == "Entrada":
                    entradas += 1
 
                elif tipo == "Salida":
                    salidas += 1
 
                    cantidad = movimiento.get("cantidad") or 0
                    precio = movimiento.get("precio")
 
                    # Si el movimiento no trae precio se usa el del producto
                    if precio is None:
                        precio = producto.get("precio") or 0
 
                    # Venta = unidades x precio; solo se suma en las salidas
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
        """Suma los totales del reporte a partir de las filas calculadas."""

 
        return {
            "productos": len(datos),
            # Stock bajo: stock actual <= stock mínimo (misma regla que el resto del sistema)
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
 
        # Una fila de la tabla por cada registro del reporte
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
 
        # Los indicadores de arriba muestran los totales
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
        """Slot para el aviso de un movimiento nuevo: recalcula el reporte."""

        self.actualizar_reporte()
 
    @Slot()
    def aplicar_filtros(self):
        """Recalcula con los datos ya cargados (sin consultar la base de datos)."""

        self._refrescar()
 
    @Slot()
    def actualizar_categorias(self):
        """
        Recarga las categorías del combo y el reporte (cuando cambian las categorías).
        """

        self.cargar_categorias()
        self.actualizar_reporte()
 
    @Slot()
    def generar_reporte(self):
        """
        Botón "Generar Reporte": valida las fechas, recarga los datos y muestra el resumen.
        """

 
        # Valida las fechas antes de consultar la base de datos
        if self.validar_fechas() is None:
            return
 
        self.cargar_datos(self._mostrar_resumen)
 
    def _mostrar_resumen(self):
        """Refresca el reporte y abre el diálogo con el resumen."""

 
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
        """
        Arma el HTML completo del reporte (encabezado, resumen y tabla). Lo usan el
        PDF y la impresión. None si las fechas son inválidas.
        """

 
        datos = self.obtener_datos_reporte()
 
        if datos is None:
            return None
 
        totales = self.calcular_totales(datos)
 
        if datos:
            detalle = self._html_tabla(datos, totales)
        else:
            detalle = self._html_sin_datos()
 
        cuerpo = (
            self._html_encabezado()
            + self._html_resumen(totales)
            + "<h2>Detalle del inventario</h2>"
            + detalle
        )
 
        return f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>{ESTILOS_REPORTE}</style>
        </head>
        <body>{cuerpo}</body>
        </html>
        """
 
    def _html_encabezado(self):
        """Título, categoría y período; `escape` evita que el texto rompa el HTML."""

 
        categoria = escape(self.reporte.currentText())
        rango = escape(self.texto_rango())
 
        return f"""
        <h1>Reporte de Inventario</h1>
        <p class="sub">
            <b>Categoría:</b> {categoria} &nbsp;|&nbsp; <b>Período:</b> {rango}
        </p>
        """
 
    def _html_resumen(self, totales):
        """Los cinco totales en una fila de tarjetas."""
 
        indicadores = [
            ("Productos", totales["productos"]),
            ("Stock bajo", totales["stock_bajo"]),
            ("Entradas", totales["entradas"]),
            ("Salidas", totales["salidas"]),
            ("Venta total", _moneda(totales["venta_total"])),
        ]
 
        celdas = "".join(
            f"""
            <td width="20%" bgcolor="{COLOR_FILA_IMPAR}" align="center">
                <div class="kpi-valor">{valor}</div>
                <div class="kpi-titulo">{titulo}</div>
            </td>
            """
            for titulo, valor in indicadores
        )
 
        return f"""
        <table width="100%" border="1" cellspacing="6" cellpadding="8"
               style="border-color:#FFFFFF;">
            <tr>{celdas}</tr>
        </table>
        """
 
    def _html_tabla(self, datos, totales):
        """
        Tabla de detalle: filas alternadas, stock bajo resaltado y fila de totales.
        """

 
        # Fila de encabezados según COLUMNAS_REPORTE
        encabezado = "".join(
            f'<th align="{alineacion}">{titulo}</th>'
            for titulo, _clave, alineacion in COLUMNAS_REPORTE
        )
 
        filas = []
        hay_stock_bajo = False
 
        for i, registro in enumerate(datos):
 
            stock_bajo = registro["stock"] <= registro["stock_minimo"]
            hay_stock_bajo = hay_stock_bajo or stock_bajo
 
            # QTextDocument no soporta tr:nth-child, por eso se alterna a mano
            if stock_bajo:
                fondo = COLOR_FILA_STOCK_BAJO
            else:
                fondo = COLOR_FILA_IMPAR if i % 2 else COLOR_FILA_PAR
 
            celdas = []
            for _titulo, clave, alineacion in COLUMNAS_REPORTE:
                texto = _formatear_celda(clave, registro[clave])
                if stock_bajo and clave == "stock":
                    texto = (
                        f'<b><font color="{COLOR_TEXTO_STOCK_BAJO}">'
                        f"{texto}</font></b>"
                    )
                celdas.append(f'<td align="{alineacion}">{texto}</td>')
 
            filas.append(f'<tr bgcolor="{fondo}">{"".join(celdas)}</tr>')
 
        # "Totales" ocupa Producto + Categoría + Stock
        pie = f"""
        <tr bgcolor="{COLOR_FILA_TOTALES}">
            <td colspan="3"><b>Totales</b></td>
            <td align="right"><b>{totales["entradas"]}</b></td>
            <td align="right"><b>{totales["salidas"]}</b></td>
            <td></td>
            <td align="right"><b>{_moneda(totales["venta_total"])}</b></td>
        </tr>
        """
 
        nota = ""
        if hay_stock_bajo:
            nota = (
                '<p class="nota">Las filas resaltadas indican productos con '
                "stock igual o inferior al stock mínimo.</p>"
            )
 
        # <thead> repite el encabezado en cada página al exportar o imprimir
        return f"""
        <table width="100%" border="1" cellspacing="0" cellpadding="6"
               style="border-color:#D5DBE3;">
            <thead><tr>{encabezado}</tr></thead>
            <tbody>{"".join(filas)}{pie}</tbody>
        </table>
        {nota}
        """
 
    @staticmethod
    def _html_sin_datos():
        """Mensaje para cuando no hay registros con los filtros elegidos."""

 
        return (
            '<p align="center"><i>'
            "No hay registros para los filtros seleccionados."
            "</i></p>"
        )
 
    @Slot()
    def exportar_pdf(self):
        """
        Pide dónde guardar el archivo y genera el PDF a partir del HTML del reporte.
        """

 
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
 
        # Impresora virtual que escribe en un archivo PDF
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(ruta)
 
        # QTextDocument convierte el HTML en un documento que se puede imprimir
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
        """Abre el diálogo de impresora y envía el reporte a imprimir."""

 
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
 
 
# Permite abrir esta página sola para probarla
if __name__ == "__main__":
 
    app = QApplication(sys.argv)
 
    ventana = Reporte()
    ventana.show()
 
    sys.exit(app.exec())