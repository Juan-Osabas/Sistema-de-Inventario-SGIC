import sys

from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QLabel,
    QMainWindow,
    QFrame,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PySide6.QtCore import Qt, Slot
    
from paginas.productos import Producto
from paginas.movimientos import Movimientos
from paginas.report import Reporte
from paginas.categorias import Categorias
from paginas.alerta import Alerta
from hilo.hilo import esperar_hilos
from estilos.estilos import (
    ESTILO_PRODUCTOS,
    ESTILO_TITULO,
    ESTILO_SUBTITULO,
    ESTILO_VENTANA_PRINCIPAL,
    ESTILO_INDICADOR_REPORTE,
    ESTILO_INDICADOR_TITULO_REPORTE,
    ESTILO_INDICADOR_VALOR_REPORTE,
    ESTILO_INDICADOR_DESCRIPCION_REPORTE,
)


class Indicador(QFrame):

    def __init__(self, titulo, valor, descripcion):

        super().__init__()

        self.titulo = QLabel(titulo)
        self.valor = QLabel(valor)
        self.descripcion = QLabel(descripcion)

        self.titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.descripcion.setAlignment(Qt.AlignmentFlag.AlignCenter)

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

        self.setStyleSheet(ESTILO_INDICADOR_REPORTE)


class Ventana_principal(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Sistema Control de Inventario")
        self.resize(1200, 750)
        self.setObjectName("ventanaPrincipal")
        self.setStyleSheet(ESTILO_VENTANA_PRINCIPAL)

        widget = QWidget()
        self.setCentralWidget(widget)

        layout_principal = QVBoxLayout(widget)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(15)

        # ---------- Encabezado ----------
        layout_encabezado = QVBoxLayout()

        titulo = QLabel("SISTEMA CONTROL DE INVENTARIO")
        subtitulo = QLabel("Pequeños negocios comerciales")

        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        titulo.setStyleSheet(ESTILO_TITULO)
        subtitulo.setStyleSheet(ESTILO_SUBTITULO)

        layout_encabezado.addWidget(titulo)
        layout_encabezado.addWidget(subtitulo)

        layout_principal.addLayout(layout_encabezado)

        layout_contenido = QHBoxLayout()
        layout_contenido.setSpacing(20)

        # ---------- Menú lateral ----------
        # La barra lateral es un widget (no solo un layout) para poder darle estilo
        self.menu_lateral = QWidget()
        self.menu_lateral.setObjectName("menuLateral")
        self.menu_lateral.setFixedWidth(230)
        self.botones_menu = []

        layout_izquierdo = QVBoxLayout(self.menu_lateral)
        layout_izquierdo.setContentsMargins(14, 20, 14, 20)
        layout_izquierdo.setSpacing(6)

        inicio = QLabel("MENÚ")
        inicio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_izquierdo.addWidget(inicio)

        opciones_menu = [
            ("Regresar al inicio", self.mostrar_inicio),
            ("Productos", self.mostrar_productos),
            ("Movimientos", self.mostrar_movimientos),
            ("Alerta", self.mostrar_alertas),
            ("Categorías", self.mostrar_categorias),
            ("Reportes", self.mostrar_reportes),
        ]

        for texto, accion in opciones_menu:
            boton = QPushButton(texto)
            boton.setMinimumHeight(45)
            boton.setCheckable(True)
            boton.setAutoExclusive(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(accion)
            layout_izquierdo.addWidget(boton)
            self.botones_menu.append(boton)

        layout_izquierdo.addStretch()

        # ---------- Página de inicio ----------
        self.stackedwidget = QStackedWidget()

        self.pagina_inicio = QWidget()
        self.pagina_inicio.setStyleSheet(ESTILO_PRODUCTOS)

        layout_inicio = QVBoxLayout(self.pagina_inicio)
        layout_inicio.setContentsMargins(20, 20, 20, 20)
        layout_inicio.setSpacing(10)

        titulo_panel = QLabel("PANEL PRINCIPAL")
        titulo_panel.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
        """)
        layout_inicio.addWidget(titulo_panel)

        layout_inicio.addWidget(QLabel("Resumen general del inventario"))

        layout_indicadores = QHBoxLayout()
        layout_indicadores.setSpacing(15)

        self.indicador_productos = Indicador(
            "Productos", "0", "Total de productos"
        )
        self.indicador_alerta = Indicador(
            "Stock Bajo", "0", "Productos con stock bajo"
        )
        self.indicador_movimientos = Indicador(
            "Movimientos", "0", "Total de movimientos"
        )

        layout_indicadores.addWidget(self.indicador_productos)
        layout_indicadores.addWidget(self.indicador_alerta)
        layout_indicadores.addWidget(self.indicador_movimientos)

        layout_inicio.addLayout(layout_indicadores)

        layout_inicio.addWidget(QLabel("Productos con stock bajo"))

        self.tabla_stock = QTableWidget()
        self.tabla_stock.setColumnCount(3)
        self.tabla_stock.setHorizontalHeaderLabels([
            "Producto",
            "Stock",
            "Stock mínimo",
        ])
        self.tabla_stock.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        # Solo es un resumen: no debe poder editarse
        self.tabla_stock.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tabla_stock.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tabla_stock.verticalHeader().setVisible(False)
        self.tabla_stock.setMinimumHeight(180)

        layout_inicio.addWidget(self.tabla_stock)

        layout_botones = QHBoxLayout()

        accesos_rapidos = [
            ("Registrar Productos", self.registrar_producto),
            ("Registrar entrada", self.registrar_entrada),
            ("Registrar Salida", self.registrar_salida),
        ]

        for texto, accion in accesos_rapidos:
            boton = QPushButton(texto)
            boton.setMinimumHeight(40)
            boton.clicked.connect(accion)
            layout_botones.addWidget(boton)

        layout_inicio.addLayout(layout_botones)

        # ---------- Páginas ----------
        self.pagina_categoria = Categorias()

        self.pagina_productos = Producto(
            self.pagina_categoria.categorias
        )

        self.pagina_categoria.productos = self.pagina_productos.productos

        self.pagina_movimientos = Movimientos(
            self.pagina_productos.productos
        )

        self.pagina_alertas = Alerta(
            self.pagina_productos.productos
        )

        self.pagina_reportes = Reporte(
            self.pagina_productos.productos,
            self.pagina_movimientos.movimientos
        )

        for pagina in (
            self.pagina_inicio,
            self.pagina_productos,
            self.pagina_movimientos,
            self.pagina_alertas,
            self.pagina_categoria,
            self.pagina_reportes,
        ):
            self.stackedwidget.addWidget(pagina)

        # Cada botón del menú queda ligado a su página para marcar la activa
        paginas_menu = [
            self.pagina_inicio,
            self.pagina_productos,
            self.pagina_movimientos,
            self.pagina_alertas,
            self.pagina_categoria,
            self.pagina_reportes,
        ]
        self.botones_por_pagina = dict(zip(paginas_menu, self.botones_menu))
        self.stackedwidget.currentChanged.connect(self.sincronizar_menu)

        # El contenido (stack) ocupa el espacio sobrante; el menú tiene ancho fijo
        layout_contenido.addWidget(self.menu_lateral)
        layout_contenido.addWidget(self.stackedwidget, 1)

        layout_principal.addLayout(layout_contenido)

        self.conectar_senales()

        self.stackedwidget.setCurrentWidget(self.pagina_inicio)
        self.sincronizar_menu(self.stackedwidget.currentIndex())

        self.actualizar_dashboard()

    # ------------------------------------------------------------------
    # Señales entre páginas
    # ------------------------------------------------------------------
    def conectar_senales(self):
        """
        Las páginas cargan sus datos en hilos, así que los resultados llegan
        cuando están listos. Por eso el dashboard se actualiza al recibir las
        señales `productos_cargados` y `movimientos_cargados`, y no justo
        después de pedir la recarga (mostraría cifras viejas).
        """

        # Categorías → Productos y Reportes
        self.pagina_categoria.categorias_actualizadas.connect(
            self.pagina_productos.actualizar_categorias
        )
        self.pagina_categoria.categorias_actualizadas.connect(
            self.pagina_reportes.actualizar_categorias
        )

        # Primera carga de categorías: llena los combos de Productos
        # sin volver a consultar los productos
        self.pagina_categoria.categorias_cargadas.connect(
            self.categorias_cargadas
        )

        # Productos: `stocks` se emite siempre junto con producto_guardado
        # y producto_eliminado, así que basta con conectar esta.
        self.pagina_productos.stocks.connect(self.refrescar_por_producto)

        # Movimientos
        self.pagina_movimientos.movimiento_registrado.connect(
            self.refrescar_por_movimiento
        )

        # Dashboard: se actualiza cuando llegan los datos
        self.pagina_productos.productos_cargados.connect(
            self.actualizar_dashboard
        )
        self.pagina_movimientos.movimientos_cargados.connect(
            self.actualizar_dashboard
        )

    def categorias_cargadas(self, categorias):

        self.pagina_productos.actualizar_categorias(
            categorias, recargar=False
        )

    def refrescar_por_producto(self, datos=None):

        self.pagina_alertas.actualizar_alertas()
        self.pagina_reportes.actualizar_reporte()

        # Si se renombró un producto, el historial debe mostrar el nombre nuevo
        self.pagina_movimientos.cargar_movimientos()

    def refrescar_por_movimiento(self, datos=None):

        # Cada página recarga en su propio hilo; el dashboard se actualiza
        # solo cuando Productos termina de cargar
        self.pagina_productos.actualizar_desde_movimiento()

        self.pagina_alertas.actualizar_alertas()
        self.pagina_reportes.actualizar_reporte()

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------
    def sincronizar_menu(self, indice):
        """Marca en el menú el botón de la página que se está mostrando."""

        pagina = self.stackedwidget.widget(indice)
        boton = self.botones_por_pagina.get(pagina)

        if boton is not None:
            boton.setChecked(True)

    @Slot()
    def mostrar_inicio(self):

        self.stackedwidget.setCurrentWidget(self.pagina_inicio)
        self.actualizar_dashboard()

    @Slot()
    def mostrar_productos(self):
        self.stackedwidget.setCurrentWidget(self.pagina_productos)

    @Slot()
    def mostrar_movimientos(self):
        self.stackedwidget.setCurrentWidget(self.pagina_movimientos)

    @Slot()
    def mostrar_alertas(self):
        self.stackedwidget.setCurrentWidget(self.pagina_alertas)

    @Slot()
    def mostrar_categorias(self):
        self.stackedwidget.setCurrentWidget(self.pagina_categoria)

    @Slot()
    def mostrar_reportes(self):
        self.stackedwidget.setCurrentWidget(self.pagina_reportes)

    @Slot()
    def registrar_producto(self):

        self.stackedwidget.setCurrentWidget(self.pagina_productos)
        self.pagina_productos.agregar_producto()

    @Slot()
    def registrar_entrada(self):

        self.stackedwidget.setCurrentWidget(self.pagina_movimientos)
        self.pagina_movimientos.registrar_entrada()

    @Slot()
    def registrar_salida(self):

        self.stackedwidget.setCurrentWidget(self.pagina_movimientos)
        self.pagina_movimientos.registrar_salida()

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def productos_activos(self):

        return [
            producto
            for producto in self.pagina_productos.productos
            if producto.get("estado", "Activo") == "Activo"
        ]

    def productos_stock_bajo(self):
        """Productos en o bajo el mínimo, los más críticos primero."""

        bajos = [
            producto
            for producto in self.productos_activos()
            if (producto["stock"] or 0) <= (producto["stock_minimo"] or 0)
        ]

        bajos.sort(
            key=lambda p: (p["stock"] or 0) - (p["stock_minimo"] or 0)
        )

        return bajos

    @Slot()
    def actualizar_indicadores(self):

        self.indicador_productos.valor.setText(
            str(len(self.productos_activos()))
        )

    @Slot()
    def actualizar_alertas(self):

        self.indicador_alerta.valor.setText(
            str(len(self.productos_stock_bajo()))
        )

    @Slot()
    def actualizar_movimientos(self):

        self.indicador_movimientos.valor.setText(
            str(len(self.pagina_movimientos.movimientos))
        )

    def actualizar_dashboard(self, datos=None):
        # Sin @Slot(): la reciben señales con y sin argumentos

        self.actualizar_indicadores()
        self.actualizar_alertas()
        self.actualizar_movimientos()
        self.actualizar_tabla_stock()

    @Slot()
    def actualizar_tabla_stock(self):

        productos_bajos = self.productos_stock_bajo()

        self.tabla_stock.setRowCount(0)

        for fila, producto in enumerate(productos_bajos):

            self.tabla_stock.insertRow(fila)

            valores = [
                str(producto["nombre"]),
                str(producto["stock"] or 0),
                str(producto["stock_minimo"] or 0),
            ]

            for columna, valor in enumerate(valores):

                item = QTableWidgetItem(valor)

                if columna > 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.tabla_stock.setItem(fila, columna, item)


if __name__ == "__main__":

    app = QApplication(sys.argv)

    ventana = Ventana_principal()
    ventana.show()

    codigo = app.exec()

    # Deja terminar las consultas pendientes antes de cerrar
    esperar_hilos()

    sys.exit(codigo)