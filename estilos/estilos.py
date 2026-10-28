"""
Estilos de la aplicación (Qt Style Sheets).

Para cambiar el aspecto de todo el sistema basta con editar la paleta de
abajo: cada color se usa en el CSS como $nombre (por ejemplo $primario).
Todos los nombres ESTILO_* se conservan, así que los demás módulos no
necesitan cambios.

Paleta base (azul pizarra):
    #06141B  #11212D  #253745  #4A5C6A  #9BA8AB  #CCD0CF
"""

from string import Template

# ----------------------------------------------------------------------
# Paleta
# ----------------------------------------------------------------------
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
}


def _t(css):
    """Reemplaza los $colores de la paleta dentro del CSS."""
    return Template(css).substitute(PALETA)


# ----------------------------------------------------------------------
# Bloques reutilizables
# ----------------------------------------------------------------------
_FUENTE = """
QWidget {
    font-family: "Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}
"""

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
    border: 1px solid $texto_tenue;
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
    background-color: $cabecera;
    color: $texto_tenue;
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
    color: $texto_tenue;
}
"""

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
    color: $texto_suave;
    padding: 11px 12px;
    border: none;
    border-bottom: 1px solid $borde;
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
    background-color: $texto_suave;
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
    background-color: $texto_suave;
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
    background-color: $cabecera;
    color: $texto;
}

QDialogButtonBox QPushButton[text="Cancelar"]:hover {
    background-color: $borde;
}
"""

_DIALOGO = _VENTANA + _INPUTS + _BOTONES_DIALOGO + _EXTRAS

# ----------------------------------------------------------------------
# Ventanas (Productos, Categorías, Movimientos, Alertas, Reportes)
# ----------------------------------------------------------------------
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
    font-size: 28px;
    font-weight: bold;
    color: $texto;
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
ESTILO_EDITAR = _t("""
QPushButton {
    background-color: $primario_suave;
    color: $primario;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: $primario_suave_hover;
}
""")

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
ESTILO_ESTADO_STOCK_BAJO = """
background-color: #F8E9E7;
color: #9B2C23;
"""

ESTILO_ESTADO_CERCA_MINIMO = """
background-color: #FBF0E4;
color: #92400E;
"""

ESTILO_ESTADO_STOCK_NORMAL = """
background-color: #CCD0CF;
color: #253745;
"""

# ----------------------------------------------------------------------
# Indicadores de Reportes e Inicio (degradado azul pizarra)
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
    color: $texto_tenue;
}
""")

# ----------------------------------------------------------------------
# Ventana principal: fondo y menú lateral oscuro
# ----------------------------------------------------------------------
ESTILO_VENTANA_PRINCIPAL = _t("""
QMainWindow#ventanaPrincipal {
    background-color: $fondo;
}

QWidget#menuLateral {
    background-color: $menu;
    border-radius: 16px;
}

QWidget#menuLateral QLabel {
    color: $texto_tenue;
    font-size: 11px;
    font-weight: bold;
    padding: 4px 8px 10px 8px;
}

QWidget#menuLateral QPushButton {
    background-color: transparent;
    color: $menu_texto;
    text-align: left;
    padding: 12px 16px;
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
""")