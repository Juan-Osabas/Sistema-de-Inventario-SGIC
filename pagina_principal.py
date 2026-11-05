"""
Ventana principal del Sistema Control de Inventario.

Está formada por dos zonas:
  * Una barra lateral oscura (izquierda) con la marca del sistema, los botones
    de navegación y la fecha.
  * Un área de contenido (derecha) que muestra una página a la vez: Inicio
    (dashboard), Productos, Movimientos, Alertas, Categorías o Reportes.

Esta ventana también conecta las páginas entre sí mediante señales, para que
cuando una cambie datos las demás se actualicen.
"""

# `sys` se usa para pasar los argumentos a QApplication y para salir con
# el código de cierre de la aplicación.
import sys

# Widgets de PySide6 (Qt) con los que se arma la interfaz.
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
# Utilidades de Qt: alineaciones, tamaños, fechas e idioma.
from PySide6.QtCore import Qt, Slot, QSize, QByteArray, QRectF, QDate, QLocale
# Clases de dibujo que se usan para crear los íconos.
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap

# El módulo de íconos SVG es opcional: si no está disponible, el sistema
# funciona igual, solo que sin íconos.
try:
    from PySide6.QtSvg import QSvgRenderer
except ImportError:
    QSvgRenderer = None

# Páginas del sistema; cada una es un widget independiente.
from paginas.productos import Producto
from paginas.movimientos import Movimientos
from paginas.report import Reporte
from paginas.categorias import Categorias
from paginas.alerta import Alerta
# Espera a que terminen las consultas en segundo plano antes de cerrar.
from hilo.hilo import esperar_hilos
# Paleta de colores y hojas de estilo (CSS de Qt) compartidas.
from estilos.estilos import (
    PALETA,
    ESTILO_PRODUCTOS,
    ESTILO_ENTRADA,
    ESTILO_SALIDA,
    ESTILO_VENTANA_PRINCIPAL,
    ESTILO_TITULO_SECCION,
    ESTILO_SUBTITULO_SECCION,
    ESTILO_TARJETA_INDICADOR,
    ESTILO_PANEL_TARJETA,
    ESTILO_TABLA_EN_TARJETA,
)


# ----------------------------------------------------------------------
# Íconos
# ----------------------------------------------------------------------
# Íconos de trazo fino (estilo "Feather") escritos como SVG. Solo se guarda el
# contenido interno de cada dibujo; el color se aplica al crearlos.
ICONOS_SVG = {
    "inicio": (
        '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
        '<polyline points="9 22 9 12 15 12 15 22"/>'
    ),
    "inventario": (
        '<line x1="16.5" y1="9.4" x2="7.5" y2="4.21"/>'
        '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 '
        '3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>'
        '<polyline points="3.27 6.96 12 12.01 20.73 6.96"/>'
        '<line x1="12" y1="22.08" x2="12" y2="12"/>'
    ),
    "movimientos": (
        '<polyline points="17 1 21 5 17 9"/>'
        '<path d="M3 11V9a4 4 0 0 1 4-4h14"/>'
        '<polyline points="7 23 3 19 7 15"/>'
        '<path d="M21 13v2a4 4 0 0 1-4 4H3"/>'
    ),
    "alerta": (
        '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 '
        '1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
        '<line x1="12" y1="9" x2="12" y2="13"/>'
        '<line x1="12" y1="17" x2="12.01" y2="17"/>'
    ),
    "categorias": (
        '<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 '
        '8.59a2 2 0 0 1 0 2.82z"/>'
        '<line x1="7" y1="7" x2="7.01" y2="7"/>'
    ),
    "reportes": (
        '<line x1="18" y1="20" x2="18" y2="10"/>'
        '<line x1="12" y1="20" x2="12" y2="4"/>'
        '<line x1="6" y1="20" x2="6" y2="14"/>'
    ),
}


def crear_pixmap(nombre, color, tamano=20):
    """
    Dibuja el ícono `nombre` del color indicado y lo devuelve como QPixmap.
    Devuelve None si no se puede dibujar (por ejemplo, si falta QtSvg).
    """

    if QSvgRenderer is None or nombre not in ICONOS_SVG:
        return None

    # Se arma un SVG completo alrededor del dibujo guardado en ICONOS_SVG
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
        'viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round">'
        f'{ICONOS_SVG[nombre]}</svg>'
    )

    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))

    # Se dibuja al doble de tamaño para que se vea nítido en pantallas HD
    pixmap = QPixmap(tamano * 2, tamano * 2)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, tamano * 2, tamano * 2))
    painter.end()

    pixmap.setDevicePixelRatio(2)

    return pixmap


def crear_icono(nombre, color_normal, color_activo):
    """
    Crea un QIcon con dos versiones: una para el botón normal y otra para el
    botón marcado (la página que se está viendo).
    """

    icono = QIcon()

    normal = crear_pixmap(nombre, color_normal)
    activo = crear_pixmap(nombre, color_activo)

    if normal is not None:
        icono.addPixmap(normal, QIcon.Mode.Normal, QIcon.State.Off)

    if activo is not None:
        icono.addPixmap(activo, QIcon.Mode.Normal, QIcon.State.On)

    return icono


# ----------------------------------------------------------------------
# Tarjeta de indicador
# ----------------------------------------------------------------------
class Indicador(QFrame):
    """
    Tarjeta que muestra una cifra importante del inventario: un ícono de
    color, un título, el valor grande y una descripción corta.

    El resto del código solo necesita `self.valor` (para cambiar la cifra con
    `.valor.setText(...)`), por eso ese nombre se conserva.
    """

    def __init__(
        self,
        titulo,
        valor,
        descripcion,
        icono="inventario",
        color=PALETA["primario"],
        fondo=PALETA["primario_suave"],
    ):

        super().__init__()

        # El nombre de objeto permite que el estilo se aplique solo a esta
        # tarjeta y no a los textos de adentro
        self.setObjectName("tarjetaIndicador")
        self.setStyleSheet(ESTILO_TARJETA_INDICADOR)

        self.titulo = QLabel(titulo)
        self.valor = QLabel(valor)
        self.descripcion = QLabel(descripcion)

        self.titulo.setObjectName("tarjetaTitulo")
        self.valor.setObjectName("tarjetaValor")
        self.descripcion.setObjectName("tarjetaDescripcion")

        # Recuadro de color con el ícono a la izquierda de la tarjeta
        self.icono = QLabel()
        self.icono.setFixedSize(52, 52)
        self.icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icono.setStyleSheet(
            f"background-color: {fondo}; border-radius: 14px;"
        )

        pixmap = crear_pixmap(icono, color, 26)

        if pixmap is not None:
            self.icono.setPixmap(pixmap)

        # Textos apilados: título, valor y descripción
        textos = QVBoxLayout()
        textos.setSpacing(2)
        textos.addWidget(self.titulo)
        textos.addWidget(self.valor)
        textos.addWidget(self.descripcion)

        # Ícono a la izquierda, textos a la derecha
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        layout.addWidget(self.icono)
        layout.addLayout(textos)
        layout.addStretch()

        self.setMinimumHeight(110)
        self.setMaximumHeight(130)


# ----------------------------------------------------------------------
# Ventana principal
# ----------------------------------------------------------------------
class Ventana_principal(QMainWindow):
    """Ventana principal: barra lateral de navegación + páginas apiladas."""


    def __init__(self):
        """Construye la ventana, crea las páginas y conecta sus señales."""


        super().__init__()

        # ---------- Ventana ----------
        self.setWindowTitle("Sistema Control de Inventario")
        self.resize(1250, 780)
        self.setMinimumSize(1050, 650)

        # El nombre de objeto hace que el fondo solo se aplique a esta ventana
        # y no a las páginas que viven dentro
        self.setObjectName("ventanaPrincipal")
        self.setStyleSheet(ESTILO_VENTANA_PRINCIPAL)

        # Widget central: contiene todo lo que se ve en la ventana
        widget = QWidget()
        self.setCentralWidget(widget)

        layout_principal = QVBoxLayout(widget)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(0)

        # Fila que coloca la barra lateral a la izquierda y el contenido a la derecha
        layout_contenido = QHBoxLayout()
        layout_contenido.setSpacing(20)

        # ---------- Barra lateral ----------
        # Es un widget (no solo un layout) para poder darle fondo y esquinas
        # redondeadas con la hoja de estilos
        self.menu_lateral = QWidget()
        self.menu_lateral.setObjectName("menuLateral")
        self.menu_lateral.setFixedWidth(240)
        self.botones_menu = []

        layout_izquierdo = QVBoxLayout(self.menu_lateral)
        layout_izquierdo.setContentsMargins(16, 22, 16, 20)
        layout_izquierdo.setSpacing(6)

        # Marca del sistema: logo cuadrado + nombre
        fila_marca = QHBoxLayout()
        fila_marca.setSpacing(12)

        logo = QLabel()
        logo.setObjectName("marcaLogo")
        logo.setFixedSize(44, 44)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pixmap_logo = crear_pixmap("inventario", "#FFFFFF", 24)

        if pixmap_logo is not None:
            logo.setPixmap(pixmap_logo)
        else:
            # Si no hay íconos disponibles, se muestran las iniciales
            logo.setText("SI")

        titulo = QLabel("Control de Inventario")
        titulo.setObjectName("marcaTitulo")

        subtitulo = QLabel("Pequeños negocios comerciales")
        subtitulo.setObjectName("marcaSubtitulo")
        subtitulo.setWordWrap(True)

        textos_marca = QVBoxLayout()
        textos_marca.setSpacing(0)
        textos_marca.addWidget(titulo)
        textos_marca.addWidget(subtitulo)

        fila_marca.addWidget(logo)
        fila_marca.addLayout(textos_marca)

        layout_izquierdo.addLayout(fila_marca)
        layout_izquierdo.addSpacing(14)

        # Línea fina que separa la marca del menú
        linea = QFrame()
        linea.setObjectName("menuLinea")
        linea.setFixedHeight(1)
        layout_izquierdo.addWidget(linea)

        # Título de la sección de navegación
        inicio = QLabel("MENÚ")
        inicio.setObjectName("menuSeccion")
        layout_izquierdo.addWidget(inicio)

        # Opciones de navegación: (texto, ícono, método que muestra la página)
        opciones_menu = [
            ("Inicio", "inicio", self.mostrar_inicio),
            ("Productos", "inventario", self.mostrar_productos),
            ("Movimientos", "movimientos", self.mostrar_movimientos),
            ("Alertas", "alerta", self.mostrar_alertas),
            ("Categorías", "categorias", self.mostrar_categorias),
            ("Reportes", "reportes", self.mostrar_reportes),
        ]

        for texto, nombre_icono, accion in opciones_menu:

            # Los espacios del inicio separan un poco el texto del ícono
            boton = QPushButton(f"  {texto}")
            boton.setIcon(crear_icono(nombre_icono, PALETA["menu_texto"], "#FFFFFF"))
            boton.setIconSize(QSize(20, 20))
            boton.setMinimumHeight(46)

            # Botones "marcables" y exclusivos: solo uno queda resaltado,
            # el de la página que se está viendo
            boton.setCheckable(True)
            boton.setAutoExclusive(True)

            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(accion)

            layout_izquierdo.addWidget(boton)
            self.botones_menu.append(boton)

        # Empuja lo que sigue hacia el final de la barra
        layout_izquierdo.addStretch()

        # Pie de la barra: fecha de hoy en español
        linea_pie = QFrame()
        linea_pie.setObjectName("menuLinea")
        linea_pie.setFixedHeight(1)
        layout_izquierdo.addWidget(linea_pie)
        layout_izquierdo.addSpacing(6)

        fecha_titulo = QLabel("HOY")
        fecha_titulo.setObjectName("menuFechaTitulo")

        fecha_hoy = QLocale(QLocale.Language.Spanish).toString(
            QDate.currentDate(), "dddd, d 'de' MMMM 'de' yyyy"
        )

        fecha = QLabel(fecha_hoy.capitalize())
        fecha.setObjectName("menuFecha")
        fecha.setWordWrap(True)

        layout_izquierdo.addWidget(fecha_titulo)
        layout_izquierdo.addWidget(fecha)

        # ---------- Área de contenido ----------
        # QStackedWidget muestra una sola página a la vez
        self.stackedwidget = QStackedWidget()

        # ---------- Página de inicio (dashboard) ----------
        self.pagina_inicio = QWidget()
        self.pagina_inicio.setStyleSheet(ESTILO_PRODUCTOS)

        layout_inicio = QVBoxLayout(self.pagina_inicio)
        layout_inicio.setContentsMargins(10, 4, 10, 10)
        layout_inicio.setSpacing(18)

        # Encabezado: título a la izquierda y accesos rápidos a la derecha
        layout_encabezado = QHBoxLayout()

        titulo_panel = QLabel("Panel principal")
        titulo_panel.setStyleSheet(ESTILO_TITULO_SECCION)

        subtitulo_panel = QLabel("Resumen general del inventario")
        subtitulo_panel.setStyleSheet(ESTILO_SUBTITULO_SECCION)

        textos_panel = QVBoxLayout()
        textos_panel.setSpacing(2)
        textos_panel.addWidget(titulo_panel)
        textos_panel.addWidget(subtitulo_panel)

        layout_encabezado.addLayout(textos_panel)
        layout_encabezado.addStretch()

        # Accesos rápidos: (texto, método, estilo propio o None = azul normal)
        accesos_rapidos = [
            ("Registrar Productos", self.registrar_producto, None),
            ("Registrar entrada", self.registrar_entrada, ESTILO_ENTRADA),
            ("Registrar Salida", self.registrar_salida, ESTILO_SALIDA),
        ]

        for texto, accion, estilo in accesos_rapidos:

            boton = QPushButton(texto)
            boton.setMinimumHeight(42)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)

            if estilo is not None:
                boton.setStyleSheet(estilo)

            boton.clicked.connect(accion)
            layout_encabezado.addWidget(boton)

        layout_inicio.addLayout(layout_encabezado)

        # Tarjetas de indicadores (cada una con su color)
        layout_indicadores = QHBoxLayout()
        layout_indicadores.setSpacing(16)

        self.indicador_productos = Indicador(
            "Productos", "0", "Total de productos",
            icono="inventario",
            color=PALETA["primario"], fondo=PALETA["primario_suave"]
        )
        self.indicador_alerta = Indicador(
            "Stock Bajo", "0", "Productos con stock bajo",
            icono="alerta",
            color=PALETA["aviso"], fondo=PALETA["aviso_suave"]
        )
        self.indicador_movimientos = Indicador(
            "Movimientos", "0", "Total de movimientos",
            icono="movimientos",
            color=PALETA["exito"], fondo=PALETA["exito_suave"]
        )

        layout_indicadores.addWidget(self.indicador_productos)
        layout_indicadores.addWidget(self.indicador_alerta)
        layout_indicadores.addWidget(self.indicador_movimientos)

        layout_inicio.addLayout(layout_indicadores)

        # Panel (tarjeta blanca) que contiene la tabla de stock bajo
        panel_stock = QFrame()
        panel_stock.setObjectName("panelTarjeta")
        panel_stock.setStyleSheet(ESTILO_PANEL_TARJETA)

        layout_panel = QVBoxLayout(panel_stock)
        layout_panel.setContentsMargins(20, 18, 20, 20)
        layout_panel.setSpacing(12)

        titulo_tabla = QLabel("Productos con stock bajo")
        titulo_tabla.setObjectName("panelTitulo")

        subtitulo_tabla = QLabel(
            "Productos que están en el mínimo o por debajo y necesitan reposición"
        )
        subtitulo_tabla.setObjectName("panelSubtitulo")

        layout_panel.addWidget(titulo_tabla)
        layout_panel.addWidget(subtitulo_tabla)

        # Tabla de resumen (solo lectura)
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
        self.tabla_stock.verticalHeader().setDefaultSectionSize(42)

        # Aspecto: filas alternadas, sin cuadrícula ni borde propio
        self.tabla_stock.setAlternatingRowColors(True)
        self.tabla_stock.setShowGrid(False)
        self.tabla_stock.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla_stock.setStyleSheet(ESTILO_TABLA_EN_TARJETA)
        self.tabla_stock.setMinimumHeight(180)

        layout_panel.addWidget(self.tabla_stock)

        # El "1" hace que el panel ocupe todo el espacio vertical sobrante
        layout_inicio.addWidget(panel_stock, 1)

        # ---------- Páginas ----------
        # Cada página carga sus propios datos (en segundo plano)
        # Cada página recibe los datos que necesita de otra (por ejemplo, Productos
        # recibe las categorías y Movimientos recibe los productos).
        self.pagina_categoria = Categorias()

        self.pagina_productos = Producto(
            self.pagina_categoria.categorias
        )

        # A Categorías se le entrega la lista de productos, que existe hasta ahora.
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

        # Se agregan todas las páginas al área de contenido
        for pagina in (
            self.pagina_inicio,
            self.pagina_productos,
            self.pagina_movimientos,
            self.pagina_alertas,
            self.pagina_categoria,
            self.pagina_reportes,
        ):
            self.stackedwidget.addWidget(pagina)

        # Cada botón del menú queda ligado a su página para marcar la activa.
        # El orden de esta lista debe coincidir con el de `opciones_menu`.
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

        # Conecta las páginas entre sí
        self.conectar_senales()

        # Arranca mostrando el inicio y con su botón marcado en el menú
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
        """Pasa las categorías recién cargadas a Productos (sin recargarlo)."""

        self.pagina_productos.actualizar_categorias(
            categorias, recargar=False
        )

    def refrescar_por_producto(self, datos=None):
        """Se ejecuta cuando se guarda, edita o elimina un producto."""

        self.pagina_alertas.actualizar_alertas()
        self.pagina_reportes.actualizar_reporte()

        # Si se renombró un producto, el historial debe mostrar el nombre nuevo
        self.pagina_movimientos.cargar_movimientos()

    def refrescar_por_movimiento(self, datos=None):
        """Se ejecuta cuando se registra una entrada o una salida."""

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
        """Muestra el dashboard y refresca sus cifras."""

        self.stackedwidget.setCurrentWidget(self.pagina_inicio)
        self.actualizar_dashboard()

    @Slot()
    def mostrar_productos(self):
        """Muestra la página de Productos."""

        self.stackedwidget.setCurrentWidget(self.pagina_productos)

    @Slot()
    def mostrar_movimientos(self):
        """Muestra la página de Movimientos."""

        self.stackedwidget.setCurrentWidget(self.pagina_movimientos)

    @Slot()
    def mostrar_alertas(self):
        """Muestra la página de Alertas."""

        self.stackedwidget.setCurrentWidget(self.pagina_alertas)

    @Slot()
    def mostrar_categorias(self):
        """Muestra la página de Categorías."""

        self.stackedwidget.setCurrentWidget(self.pagina_categoria)

    @Slot()
    def mostrar_reportes(self):
        """Muestra la página de Reportes."""

        self.stackedwidget.setCurrentWidget(self.pagina_reportes)

    @Slot()
    def registrar_producto(self):
        """Acceso rápido: va a Productos y abre el formulario de nuevo producto."""

        self.stackedwidget.setCurrentWidget(self.pagina_productos)
        self.pagina_productos.agregar_producto()

    @Slot()
    def registrar_entrada(self):
        """Acceso rápido: va a Movimientos y abre el formulario de entrada."""

        self.stackedwidget.setCurrentWidget(self.pagina_movimientos)
        self.pagina_movimientos.registrar_entrada()

    @Slot()
    def registrar_salida(self):
        """Acceso rápido: va a Movimientos y abre el formulario de salida."""

        self.stackedwidget.setCurrentWidget(self.pagina_movimientos)
        self.pagina_movimientos.registrar_salida()

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def productos_activos(self):
        """Lista de productos cuyo estado es "Activo"."""

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
        """Actualiza la tarjeta con el total de productos activos."""

        self.indicador_productos.valor.setText(
            str(len(self.productos_activos()))
        )

    @Slot()
    def actualizar_alertas(self):
        """Actualiza la tarjeta con la cantidad de productos con stock bajo."""

        self.indicador_alerta.valor.setText(
            str(len(self.productos_stock_bajo()))
        )

    @Slot()
    def actualizar_movimientos(self):
        """Actualiza la tarjeta con el total de movimientos registrados."""

        self.indicador_movimientos.valor.setText(
            str(len(self.pagina_movimientos.movimientos))
        )

    def actualizar_dashboard(self, datos=None):
        """Refresca todas las tarjetas y la tabla del inicio."""
        # Sin @Slot(): la reciben señales con y sin argumentos

        self.actualizar_indicadores()
        self.actualizar_alertas()
        self.actualizar_movimientos()
        self.actualizar_tabla_stock()

    @Slot()
    def actualizar_tabla_stock(self):
        """Llena la tabla del inicio con los productos de stock bajo."""

        productos_bajos = self.productos_stock_bajo()

        # Se vacía la tabla antes de volver a llenarla
        self.tabla_stock.setRowCount(0)

        for fila, producto in enumerate(productos_bajos):

            self.tabla_stock.insertRow(fila)

            # Valores de la fila (`or 0` por si la base de datos devuelve NULL)
            valores = [
                str(producto["nombre"]),
                str(producto["stock"] or 0),
                str(producto["stock_minimo"] or 0),
            ]

            for columna, valor in enumerate(valores):

                item = QTableWidgetItem(valor)

                # Las cifras van centradas
                if columna > 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # El stock actual se resalta en rojo y negrita
                if columna == 1:
                    item.setForeground(QColor(PALETA["peligro_hover"]))

                    fuente = item.font()
                    fuente.setBold(True)
                    item.setFont(fuente)

                self.tabla_stock.setItem(fila, columna, item)


# Punto de entrada: crea la aplicación Qt, muestra la ventana y arranca el
# bucle de eventos.
if __name__ == "__main__":

    app = QApplication(sys.argv)

    ventana = Ventana_principal()
    ventana.show()

    # exec() bloquea hasta que se cierra la ventana y devuelve el código de salida
    codigo = app.exec()

    # Deja terminar las consultas pendientes antes de cerrar
    esperar_hilos()

    sys.exit(codigo)