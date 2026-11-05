"""
Estilos de la aplicación (Qt Style Sheets).

Para cambiar el aspecto de todo el sistema basta con editar la paleta de
abajo: cada color se usa en el CSS como $nombre (por ejemplo $primario).
Todos los nombres ESTILO_* se conservan, así que los demás módulos no
necesitan cambios.
"""

# Template permite escribir $nombre dentro del CSS y reemplazarlo por un color
from string import Template

# ----------------------------------------------------------------------
# Paleta
# ----------------------------------------------------------------------
# Diccionario de colores. También se usa desde el código Python
# (por ejemplo PALETA["primario"] en la ventana principal).
PALETA = {
    # Marca
    "primario": "#253745",
    "primario_claro": "#4A5C6A",
    "primario_hover": "#11212D",
    "primario_press": "#06141B",
    "primario_suave": "#E6E9E9",
    "primario_suave_hover": "#CCD0CF",

    # Fondos y bordes
    "fondo": "#E9ECEC",
    "superficie": "#FFFFFF",
    "cabecera": "#DDE1E1",
    "fila_alterna": "#F4F6F6",
    "borde": "#CCD0CF",
    "borde_suave": "#E1E5E5",
    "seleccion": "#CCD0CF",

    # Texto
    "texto": "#11212D",
    "texto_suave": "#4A5C6A",
    "texto_tenue": "#9BA8AB",

    # Estados
    "peligro": "#B83A32",
    "peligro_suave": "#F8E9E7",
    "peligro_suave_hover": "#F1D5D1",
    "aviso": "#B45309",
    "aviso_claro": "#D98A2B",
    "aviso_hover": "#92400E",
    "aviso_suave": "#FBF0E4",
    "aviso_suave_hover": "#F5E0C8",
    "exito": "#2F7D5B",
    "exito_hover": "#256549",

    # Menú lateral
    "menu": "#06141B",
    "menu_hover": "#11212D",
    "menu_activo": "#4A5C6A",
    "menu_texto": "#CCD0CF",

    # Barras de desplazamiento
    "scroll": "#9BA8AB",

    # --- Añadidos para el diseño nuevo (derivados de tu paleta) ---
    "gris_suave": "#E6E9E9",        # botón Cancelar y campos deshabilitados
    "cabecera_texto": "#253745",    # texto del encabezado de las tablas
    "cabecera_borde": "#CCD0CF",    # línea bajo el encabezado de las tablas
    "peligro_hover": "#962E28",     # rojo oscuro (stock crítico)
    "exito_suave": "#E5F1EC",       # fondo suave del verde
    "scroll_hover": "#7C8B8F",      # barra de desplazamiento al pasar el cursor
}


def _t(css):
    """Reemplaza los $colores de la paleta dentro del CSS."""
    return Template(css).substitute(PALETA)


# ----------------------------------------------------------------------
# Bloques reutilizables
# ----------------------------------------------------------------------
# Bloques reutilizables de CSS: cada uno se combina con "+" en los estilos de
# cada página.
#
# _FUENTE: tipografía base de todos los widgets
_FUENTE = """
QWidget {
    font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}
"""

# _VENTANA: fondo de ventanas y diálogos, y color de las etiquetas
_VENTANA = """
QMainWindow {
    background-color: $fondo;
}

QDialog {
    background-color: $superficie;
}

QLabel {
    color: $texto;
}
"""

# _INPUTS: campos de texto, combos y spin boxes (normal, hover, foco y deshabilitado)
_INPUTS = """
QLineEdit,
QComboBox,
QSpinBox,
QDoubleSpinBox {
    background-color: $superficie;
    border: 1px solid $borde;
    border-radius: 8px;
    padding: 8px 12px;
    color: $texto;
    selection-background-color: $seleccion;
    selection-color: $texto;
}

QLineEdit:hover,
QComboBox:hover,
QSpinBox:hover,
QDoubleSpinBox:hover {
    border: 1px solid $scroll_hover;
}

QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {
    border: 1px solid $primario;
}

QLineEdit:disabled,
QComboBox:disabled,
QSpinBox:disabled,
QDoubleSpinBox:disabled {
    background-color: $gris_suave;
    color: $texto_suave;
}

QComboBox QAbstractItemView {
    background-color: $superficie;
    color: $texto;
    border: 1px solid $borde;
    selection-background-color: $seleccion;
    selection-color: $texto;
    outline: none;
    padding: 4px;
}
"""

# _BOTON: botón principal (normal, hover, presionado y deshabilitado)
_BOTON = """
QPushButton {
    background-color: $primario;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: $primario_hover;
}

QPushButton:pressed {
    background-color: $primario_press;
}

QPushButton:disabled {
    background-color: $borde;
    color: $texto_suave;
}
"""

# _TABLA: tablas (filas alternadas y encabezado con esquinas redondeadas)
_TABLA = """
QTableWidget {
    background-color: $superficie;
    alternate-background-color: $fila_alterna;
    border: 1px solid $borde;
    border-radius: 12px;
    gridline-color: $borde_suave;
    color: $texto;
    selection-background-color: $seleccion;
    selection-color: $texto;
    outline: none;
}

QTableWidget::item {
    padding: 4px 8px;
}

QTableWidget::item:selected {
    background-color: $seleccion;
    color: $texto;
}

QHeaderView::section {
    background-color: $cabecera;
    color: $cabecera_texto;
    padding: 11px 12px;
    border: none;
    border-bottom: 1px solid $cabecera_borde;
    font-weight: bold;
}

QHeaderView::section:horizontal:first {
    border-top-left-radius: 11px;
}

QHeaderView::section:horizontal:last {
    border-top-right-radius: 11px;
}

QTableCornerButton::section {
    background-color: $cabecera;
    border: none;
}
"""

# _SCROLL: barras de desplazamiento delgadas y sin flechas
_SCROLL = """
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background-color: $scroll;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: $scroll_hover;
}

QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}

QScrollBar::handle:horizontal {
    background-color: $scroll;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background-color: $scroll_hover;
}

QScrollBar::add-line,
QScrollBar::sub-line {
    width: 0px;
    height: 0px;
}

QScrollBar::add-page,
QScrollBar::sub-page {
    background: transparent;
}
"""

# _EXTRAS: tooltips y cuadros de mensaje
_EXTRAS = """
QToolTip {
    background-color: $texto;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 6px 8px;
}

QMessageBox {
    background-color: $superficie;
}

QMessageBox QPushButton {
    min-width: 84px;
}
"""

# Botones Guardar / Aceptar (azul) y Cancelar (gris) de los diálogos
_BOTONES_DIALOGO = """
QDialogButtonBox QPushButton {
    background-color: $primario;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    min-width: 80px;
    font-weight: bold;
}

QDialogButtonBox QPushButton:hover {
    background-color: $primario_hover;
}

QDialogButtonBox QPushButton:pressed {
    background-color: $primario_press;
}

QDialogButtonBox QPushButton[text="Cancelar"] {
    background-color: $gris_suave;
    color: $texto;
}

QDialogButtonBox QPushButton[text="Cancelar"]:hover {
    background-color: $borde;
}
"""

# _DIALOGO: estilo completo de un diálogo = ventana + campos + botones + extras
_DIALOGO = _VENTANA + _INPUTS + _BOTONES_DIALOGO + _EXTRAS

# ----------------------------------------------------------------------
# Ventanas (Productos, Categorías, Movimientos, Alertas, Reportes)
# ----------------------------------------------------------------------
# Estilo base de las páginas (fuente, campos, botones, tablas, scroll y extras).
# Las páginas de Categorías y Movimientos usan este mismo estilo.
ESTILO_PRODUCTOS = _t(
    _FUENTE + _VENTANA + _INPUTS + _BOTON + _TABLA + _SCROLL + _EXTRAS
)

ESTILO_CATEGORIAS = ESTILO_PRODUCTOS
ESTILO_MOVIMIENTOS = ESTILO_PRODUCTOS

# ----------------------------------------------------------------------
# Títulos
# ----------------------------------------------------------------------
ESTILO_TITULO = _t("""
QLabel {
    font-size: 26px;
    font-weight: bold;
    color: $primario_hover;
}
""")

ESTILO_SUBTITULO = _t("""
QLabel {
    font-size: 14px;
    color: $texto_suave;
}
""")

# ----------------------------------------------------------------------
# Botones de acción dentro de las tablas (estilo "suave")
# ----------------------------------------------------------------------
# ESTILO_EDITAR: botón "Editar" de las tablas de Productos y Categorías
ESTILO_EDITAR = _t("""
QPushButton {
    background-color: $primario_suave;
    color: $primario_hover;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: $primario_suave_hover;
}
""")

# ESTILO_ELIMINAR: botón "Eliminar" de la tabla de Productos
ESTILO_ELIMINAR = _t("""
QPushButton {
    background-color: $peligro_suave;
    color: $peligro;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: $peligro_suave_hover;
}
""")

# ESTILO_INACTIVAR: botón "Inactivar / Activar" de la tabla de Categorías
ESTILO_INACTIVAR = _t("""
QPushButton {
    background-color: $aviso_suave;
    color: $aviso;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: $aviso_suave_hover;
}
""")

# ----------------------------------------------------------------------
# Botones Entrada / Salida
# ----------------------------------------------------------------------
# ESTILO_ENTRADA: botón de entrada (página Movimientos y acceso rápido del inicio)
ESTILO_ENTRADA = _t("""
QPushButton {
    background-color: $exito;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: $exito_hover;
}
""")

# ESTILO_SALIDA: botón de salida (página Movimientos y acceso rápido del inicio)
ESTILO_SALIDA = _t("""
QPushButton {
    background-color: $aviso;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: $aviso_hover;
}
""")

# ----------------------------------------------------------------------
# Formularios (diálogos)
# ----------------------------------------------------------------------
ESTILO_FORMULARIO_CATEGORIA = _t(_DIALOGO)
ESTILO_FORMULARIO_MOVIMIENTO = _t(_DIALOGO)

# ----------------------------------------------------------------------
# Indicadores de la página de Alertas (degradado naranja)
# ----------------------------------------------------------------------
ESTILO_INDICADOR_ALERTAS = _t("""
QFrame {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 $aviso_claro, stop: 1 $aviso
    );
    border: none;
    border-radius: 14px;
}

QLabel {
    background-color: transparent;
    border: none;
    color: #FFFFFF;
}
""")

# Textos de la tarjeta indicadora: título, valor y descripción
ESTILO_INDICADOR_TITULO = """
font-size: 15px;
font-weight: bold;
color: #FFFFFF;
"""

ESTILO_INDICADOR_VALOR = """
font-size: 32px;
font-weight: bold;
color: #FFFFFF;
"""

ESTILO_INDICADOR_DESCRIPCION = """
font-size: 12px;
color: rgba(255, 255, 255, 215);
"""

# Estados de stock (texto + fondo)
ESTILO_ESTADO_STOCK_BAJO = _t("""
background-color: $peligro_suave;
color: $peligro;
""")

ESTILO_ESTADO_CERCA_MINIMO = _t("""
background-color: $aviso_suave;
color: $aviso;
""")

ESTILO_ESTADO_STOCK_NORMAL = _t("""
background-color: $primario_suave;
color: $primario_hover;
""")

# ----------------------------------------------------------------------
# Indicadores de Reportes e Inicio (degradado azul)
# ----------------------------------------------------------------------
ESTILO_INDICADOR_REPORTE = _t("""
QFrame {
    background-color: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 $primario_claro, stop: 1 $primario
    );
    border: none;
    border-radius: 14px;
}

QLabel {
    background-color: transparent;
    border: none;
    color: #FFFFFF;
}
""")

# Los textos de las tarjetas de Reportes reutilizan los de Alertas
ESTILO_INDICADOR_TITULO_REPORTE = ESTILO_INDICADOR_TITULO
ESTILO_INDICADOR_VALOR_REPORTE = ESTILO_INDICADOR_VALOR
ESTILO_INDICADOR_DESCRIPCION_REPORTE = ESTILO_INDICADOR_DESCRIPCION

# ----------------------------------------------------------------------
# Diálogo de Reportes
# ----------------------------------------------------------------------
ESTILO_DIALOGO_REPORTE = _t(_DIALOGO)

ESTILO_GRUPO_REPORTE = _t("""
QGroupBox {
    background-color: $superficie;
    border: 1px solid $borde;
    border-radius: 12px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    color: $primario;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
}
""")

ESTILO_BOTONES_REPORTE = _t(_BOTONES_DIALOGO)

ESTILO_BOTONES_PAGINA_REPORTE = _t("""
QPushButton {
    background-color: $primario;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: $primario_hover;
}

QPushButton:pressed {
    background-color: $primario_press;
}

QPushButton:disabled {
    background-color: $borde;
    color: $texto_suave;
}
""")

# ----------------------------------------------------------------------
# Ventana principal: fondo y menú lateral oscuro
# ----------------------------------------------------------------------
ESTILO_VENTANA_PRINCIPAL = _t("""
QMainWindow#ventanaPrincipal {
    background-color: $fondo;
}

/* ---- Barra lateral ---- */
QWidget#menuLateral {
    background-color: $menu;
    border-radius: 18px;
}

/* Marca (logo + nombre del sistema) */
QLabel#marcaLogo {
    background-color: $menu_activo;
    border-radius: 12px;
    color: #FFFFFF;
    font-size: 15px;
    font-weight: bold;
}

QLabel#marcaTitulo {
    color: #FFFFFF;
    font-size: 15px;
    font-weight: bold;
}

QLabel#marcaSubtitulo {
    color: $texto_tenue;
    font-size: 11px;
}

/* Línea separadora */
QFrame#menuLinea {
    background-color: $menu_hover;
    border: none;
}

/* Título de sección ("MENÚ") */
QLabel#menuSeccion {
    color: $texto_tenue;
    font-size: 11px;
    font-weight: bold;
    padding: 8px 12px 4px 12px;
}

/* Botones de navegación */
QWidget#menuLateral QPushButton {
    background-color: transparent;
    color: $menu_texto;
    text-align: left;
    padding: 12px 14px;
    border: none;
    border-radius: 10px;
    font-size: 14px;
    font-weight: normal;
}

QWidget#menuLateral QPushButton:hover {
    background-color: $menu_hover;
    color: #FFFFFF;
}

QWidget#menuLateral QPushButton:checked {
    background-color: $menu_activo;
    color: #FFFFFF;
    font-weight: bold;
}

/* Pie de la barra (fecha) */
QLabel#menuFechaTitulo {
    color: $texto_tenue;
    font-size: 10px;
    font-weight: bold;
    padding-left: 4px;
}

QLabel#menuFecha {
    color: $menu_texto;
    font-size: 12px;
    padding-left: 4px;
}
""")

# ----------------------------------------------------------------------
# Página de inicio: títulos, tarjetas y paneles
# ----------------------------------------------------------------------
ESTILO_TITULO_SECCION = _t("""
QLabel {
    font-size: 24px;
    font-weight: bold;
    color: $primario_hover;
}
""")

ESTILO_SUBTITULO_SECCION = _t("""
QLabel {
    font-size: 13px;
    color: $texto_suave;
}
""")

# Tarjeta de indicador (KPI): fondo blanco, borde fino y esquinas redondeadas
ESTILO_TARJETA_INDICADOR = _t("""
QFrame#tarjetaIndicador {
    background-color: $superficie;
    border: 1px solid $borde;
    border-radius: 16px;
}

QLabel#tarjetaTitulo {
    font-size: 13px;
    font-weight: bold;
    color: $texto_suave;
}

QLabel#tarjetaValor {
    font-size: 32px;
    font-weight: bold;
    color: $texto;
}

QLabel#tarjetaDescripcion {
    font-size: 12px;
    color: $texto_suave;
}
""")

# Panel contenedor (tarjeta grande que envuelve una tabla)
ESTILO_PANEL_TARJETA = _t("""
QFrame#panelTarjeta {
    background-color: $superficie;
    border: 1px solid $borde;
    border-radius: 16px;
}

QLabel#panelTitulo {
    font-size: 16px;
    font-weight: bold;
    color: $texto;
}

QLabel#panelSubtitulo {
    font-size: 12px;
    color: $texto_suave;
}
""")

# La tabla dentro de un panel no necesita su propio borde
ESTILO_TABLA_EN_TARJETA = """
QTableWidget {
    border: none;
}
"""



# ----------------------------------------------------------------------
# Datos de la página de Reportes (no son estilos)
# Se importan desde report.py, por eso viven en este archivo.
# ----------------------------------------------------------------------
# TODAS_CATEGORIAS: primera opción del combo de categorías (sin filtrar)
TODAS_CATEGORIAS = "Todas las categorías"
 
# Nombres de las categorías activas, para el combo del reporte
SQL_CATEGORIAS = """
    SELECT nombre
    FROM categorias
    WHERE estado = 'Activo'
    ORDER BY nombre
"""
 
# Productos activos con el nombre de su categoría
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
 
# Todos los movimientos con código y nombre de su producto, del más viejo al más nuevo
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
 
# Estilo propio de la ventana de Reportes (fondo blanco, campos y combos).
# Se suma a ESTILO_PRODUCTOS.
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
 
 
# ----------------------------------------------------------------------
# Reporte HTML / PDF
# QTextDocument solo soporta un subconjunto de HTML y CSS (sin flex, grid
# ni nth-child), por eso se usan tablas y atributos clásicos.
# ----------------------------------------------------------------------
ESTILOS_REPORTE = """
    body { font-family: Arial; font-size: 10pt; color: #2C3E50; }
    h1 { text-align: center; color: #2C3E50; margin-bottom: 2px; }
    h2 { color: #2C3E50; margin-top: 18px; margin-bottom: 6px; }
    .sub { text-align: center; color: #7F8C8D; font-size: 9pt; }
    th { background-color: #3498DB; color: white; padding: 6px; }
    td { padding: 5px; }
    .kpi-valor { font-size: 15pt; font-weight: bold; text-align: center; }
    .kpi-titulo { font-size: 8pt; color: #7F8C8D; text-align: center; }
    .nota { font-size: 8pt; color: #7F8C8D; }
"""
 
# Colores de las filas del reporte HTML: par, impar, stock bajo y totales
COLOR_FILA_PAR = "#FFFFFF"
COLOR_FILA_IMPAR = "#F5F7FA"
COLOR_FILA_STOCK_BAJO = "#FDECEA"
COLOR_TEXTO_STOCK_BAJO = "#C0392B"
COLOR_FILA_TOTALES = "#E8EEF4"
 
# (título, clave del registro, alineación)
COLUMNAS_REPORTE = [
    ("Producto", "producto", "left"),
    ("Categoría", "categoria", "left"),
    ("Stock", "stock", "right"),
    ("Entradas", "entradas", "right"),
    ("Salidas", "salidas", "right"),
    ("Precio", "precio", "right"),
    ("Venta", "venta", "right"),
]
 