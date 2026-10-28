import sys

from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QHeaderView,
    QTableWidgetItem,
    QMessageBox,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

from paginas.conexion import ConexionMySQL
from hilo.hilo import consultar, Cargador
from estilos.estilos import (
    ESTILO_CATEGORIAS,
    ESTILO_EDITAR,
    ESTILO_INACTIVAR,
    ESTILO_FORMULARIO_CATEGORIA,
    ESTILO_TITULO,
    ESTILO_SUBTITULO,
)

SQL_CATEGORIAS = """
    SELECT id_categoria AS id,
           nombre,
           descripcion,
           estado
    FROM categorias
    ORDER BY id_categoria
"""


class FormularioCategoria(QDialog):

    def __init__(self, parent=None, categoria=None):
        super().__init__(parent)
        self.setStyleSheet(ESTILO_FORMULARIO_CATEGORIA)

        self.setWindowTitle(
            "Editar Categoría" if categoria else "Nueva Categoría"
        )
        self.setModal(True)

        layout = QVBoxLayout(self)
        formulario = QFormLayout()

        self.nombre = QLineEdit()
        self.nombre.setPlaceholderText("Nombre de la categoría")

        self.descripcion = QLineEdit()
        self.descripcion.setPlaceholderText("Descripción de la categoría")

        formulario.addRow("Nombre:", self.nombre)
        formulario.addRow("Descripción:", self.descripcion)

        layout.addLayout(formulario)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        botones.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")

        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)

        layout.addWidget(botones)

        if categoria:
            self.nombre.setText(categoria["nombre"] or "")
            self.descripcion.setText(categoria["descripcion"] or "")

    def accept(self):
        # Valida antes de cerrar, así el usuario no pierde lo que escribió
        if not self.nombre.text().strip():
            QMessageBox.warning(
                self,
                "Dato requerido",
                "El nombre de la categoría es obligatorio."
            )
            self.nombre.setFocus()
            return

        super().accept()

    def obtener_datos(self):

        return {
            "nombre": self.nombre.text().strip(),
            "descripcion": self.descripcion.text().strip(),
        }


class Categorias(QMainWindow):

    categorias_actualizadas = Signal(list)
    categorias_cargadas = Signal(list)

    def __init__(self, productos=None):

        super().__init__()
        self.setStyleSheet(ESTILO_CATEGORIAS)

        self.productos = productos if productos is not None else []
        self.categorias = []  # evita AttributeError si falla la primera carga
        self._cargador = Cargador()

        self.db = ConexionMySQL()

        self.setWindowTitle("Categorías")
        self.resize(900, 600)

        widget = QWidget()
        self.setCentralWidget(widget)

        layout_principal = QVBoxLayout(widget)
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(15)

        titulo = QLabel("Categorías")
        subtitulo = QLabel("Organización de los productos del inventario")

        titulo.setStyleSheet(ESTILO_TITULO)
        subtitulo.setStyleSheet(ESTILO_SUBTITULO)

        layout_principal.addWidget(titulo)
        layout_principal.addWidget(subtitulo)

        layout_buscar = QHBoxLayout()

        self.buscar = QLineEdit()
        self.buscar.setPlaceholderText("Buscar categoría...")
        self.buscar.setClearButtonEnabled(True)
        self.buscar.textChanged.connect(self.filtrar_tabla)

        nueva_categoria = QPushButton("+ Nueva Categoría")
        nueva_categoria.clicked.connect(self.agregar_categoria)

        layout_buscar.addWidget(self.buscar)
        layout_buscar.addWidget(nueva_categoria)

        layout_principal.addLayout(layout_buscar)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "ID",
            "Categoría",
            "Descripción",
            "Estado",
            "Acciones",
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
        self.tabla.verticalHeader().setVisible(False)

        # Filas más altas y columna de acciones con ancho fijo para que
        # los botones Editar / Inactivar no se corten
        self.tabla.verticalHeader().setDefaultSectionSize(48)
        self.tabla.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Fixed
        )
        self.tabla.setColumnWidth(4, 220)

        layout_principal.addWidget(self.tabla)

        self.cargar_categorias()

    # ------------------------------------------------------------------
    # Auxiliares
    # ------------------------------------------------------------------
    def _conectar_o_avisar(self):
        """Devuelve la conexión o muestra el error y devuelve None."""

        conexion = self.db.conectar()

        if conexion is None:
            QMessageBox.critical(
                self,
                "Error de conexión",
                "No se pudo conectar con la base de datos."
            )

        return conexion

    @staticmethod
    def _nombre_duplicado(cursor, nombre, excluir_id=None):

        if excluir_id is None:
            cursor.execute(
                """
                SELECT id_categoria
                FROM categorias
                WHERE LOWER(nombre) = LOWER(%s)
                """,
                (nombre,)
            )
        else:
            cursor.execute(
                """
                SELECT id_categoria
                FROM categorias
                WHERE LOWER(nombre) = LOWER(%s)
                AND id_categoria != %s
                """,
                (nombre, excluir_id)
            )

        return cursor.fetchone() is not None

    def _recargar(self):
        """Recarga en segundo plano y avisa a otras ventanas al terminar."""

        self.cargar_categorias(
            lambda: self.categorias_actualizadas.emit(self.categorias)
        )

    def obtener_categorias_activas(self):

        return [
            categoria["nombre"]
            for categoria in self.categorias
            if categoria["estado"] == "Activo"
        ]

    # ------------------------------------------------------------------
    # Tabla
    # ------------------------------------------------------------------
    def actualizar_tabla(self):

        self.tabla.setRowCount(0)

        for fila, categoria in enumerate(self.categorias):

            self.tabla.insertRow(fila)

            valores = [
                str(categoria["id"]),
                categoria["nombre"] or "",
                categoria["descripcion"] or "",  # puede venir None de la BD
                categoria["estado"] or "",
            ]

            inactiva = categoria["estado"] != "Activo"

            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(valor)

                if inactiva:
                    item.setForeground(QColor("#90A4AE"))

                self.tabla.setItem(fila, columna, item)

            contenedor = QWidget()

            layout = QHBoxLayout(contenedor)
            layout.setContentsMargins(5, 2, 5, 2)
            layout.setSpacing(5)

            editar = QPushButton("Editar")
            # El botón cambia según el estado: antes siempre decía "Inactivar"
            inactivar = QPushButton("Activar" if inactiva else "Inactivar")

            editar.clicked.connect(
                lambda checked=False, p=categoria: self.editar_categoria(p)
            )
            inactivar.clicked.connect(
                lambda checked=False, p=categoria: self.inactivar_categoria(p)
            )

            layout.addWidget(editar)
            layout.addWidget(inactivar)

            self.tabla.setCellWidget(fila, 4, contenedor)

            editar.setStyleSheet(ESTILO_EDITAR)
            inactivar.setStyleSheet(ESTILO_INACTIVAR)

        # Mantiene el filtro de búsqueda después de recargar
        self.filtrar_tabla(self.buscar.text())

    def filtrar_tabla(self, texto):

        texto = texto.lower().strip()

        for fila in range(self.tabla.rowCount()):

            nombre = self.tabla.item(fila, 1)
            descripcion = self.tabla.item(fila, 2)

            contenido = " ".join(
                item.text().lower()
                for item in (nombre, descripcion)
                if item
            )

            self.tabla.setRowHidden(fila, texto not in contenido)

    # ------------------------------------------------------------------
    # Base de datos
    # ------------------------------------------------------------------
    def cargar_categorias(self, al_terminar=None):
        """Lee las categorías en un hilo y refresca la tabla al terminar."""

        self._cargador.cargar(
            lambda: consultar(SQL_CATEGORIAS),
            lambda filas: self._categorias_listas(filas, al_terminar),
            self._error_carga,
        )

    def _categorias_listas(self, filas, al_terminar=None):

        self.categorias = filas

        self.actualizar_tabla()
        self.categorias_cargadas.emit(self.categorias)

        if al_terminar is not None:
            al_terminar()

    def _error_carga(self, mensaje):

        QMessageBox.critical(
            self,
            "Error al cargar categorías",
            f"No se pudieron cargar las categorías:\n{mensaje}"
        )

    def agregar_categoria(self):

        dialogo = FormularioCategoria(self)

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        datos = dialogo.obtener_datos()

        if not datos["nombre"]:
            QMessageBox.warning(
                self,
                "Dato requerido",
                "El nombre de la categoría es obligatorio."
            )
            return

        conexion = self._conectar_o_avisar()

        if conexion is None:
            return

        try:
            cursor = conexion.cursor()

            if self._nombre_duplicado(cursor, datos["nombre"]):
                cursor.close()
                QMessageBox.warning(
                    self,
                    "Categoría duplicada",
                    "Ya existe una categoría con ese nombre."
                )
                return

            cursor.execute(
                """
                INSERT INTO categorias
                (nombre, descripcion, estado)
                VALUES (%s, %s, %s)
                """,
                (datos["nombre"], datos["descripcion"], "Activo")
            )

            conexion.commit()
            cursor.close()

            self._recargar()

            QMessageBox.information(
                self,
                "Categoría registrada",
                "La categoría se registró correctamente."
            )

        except Exception as e:
            conexion.rollback()

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo registrar la categoría:\n{e}"
            )

        finally:
            self.db.cerrar()

    def editar_categoria(self, categoria):

        dialogo = FormularioCategoria(self, categoria)

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        datos = dialogo.obtener_datos()

        if not datos["nombre"]:
            QMessageBox.warning(
                self,
                "Dato requerido",
                "El nombre de la categoría es obligatorio."
            )
            return

        conexion = self._conectar_o_avisar()

        if conexion is None:
            return

        try:
            cursor = conexion.cursor()

            if self._nombre_duplicado(
                cursor, datos["nombre"], categoria["id"]
            ):
                cursor.close()
                QMessageBox.warning(
                    self,
                    "Categoría duplicada",
                    "Ya existe otra categoría con ese nombre."
                )
                return

            cursor.execute(
                """
                UPDATE categorias
                SET nombre = %s,
                    descripcion = %s
                WHERE id_categoria = %s
                """,
                (datos["nombre"], datos["descripcion"], categoria["id"])
            )

            conexion.commit()
            cursor.close()

            self._recargar()

            QMessageBox.information(
                self,
                "Categoría actualizada",
                "La categoría se actualizó correctamente."
            )

        except Exception as e:
            conexion.rollback()

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo actualizar la categoría:\n{e}"
            )

        finally:
            self.db.cerrar()

    def inactivar_categoria(self, categoria):

        if categoria["estado"] == "Activo":
            nuevo_estado = "Inactivo"
            mensaje = "¿Deseas inactivar esta categoría?"
        else:
            nuevo_estado = "Activo"
            mensaje = "¿Deseas activar esta categoría?"

        respuesta = QMessageBox.question(
            self,
            "Cambiar estado",
            mensaje,
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
                UPDATE categorias
                SET estado = %s
                WHERE id_categoria = %s
                """,
                (nuevo_estado, categoria["id"])
            )

            conexion.commit()
            cursor.close()

            self._recargar()

        except Exception as e:
            conexion.rollback()

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo cambiar el estado:\n{e}"
            )

        finally:
            self.db.cerrar()


if __name__ == "__main__":

    app = QApplication(sys.argv)

    ventana = Categorias()
    ventana.show()

    sys.exit(app.exec())