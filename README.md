# Sistema Control de Inventario

Aplicación de escritorio para pequeños negocios comerciales. Permite gestionar
productos, categorías, entradas y salidas de inventario, alertas de stock bajo
y reportes (con exportación a PDF e impresión).

Hecha con **Python**, **PySide6** (interfaz) y **MySQL** (base de datos).

## Requisitos

- Python 3.10 o superior
- MySQL Server en funcionamiento
- Las librerías de `requirements.txt`

## Instalación

1. Clonar el repositorio y entrar a la carpeta:

   ```bash
   git clone https://github.com/Juan-Osabas/Sistema-de-Inventario-SGIC.git
   cd TU_REPOSITORIO
   ```

2. (Recomendado) Crear y activar un entorno virtual:

   ```bash
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # Linux / macOS
   source .venv/bin/activate
   ```

3. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

## Configuración de la base de datos

1. Crear la base de datos y sus tablas (`productos`, `categorias`, `movimientos`)
   ejecutando el script SQL del proyecto en MySQL.

2. Copiar `.env.example` como `.env` y escribir los datos reales:

   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=tu_contraseña
   DB_NAME=nombre_de_tu_base_de_datos
   ```

   > El archivo `.env` contiene la contraseña y **no se sube a GitHub**.

3. Comprobar que la conexión funciona:

   ```bash
   python probar_conexion.py
   ```

   Debe mostrar `OK: conectado a la base de datos '...'`.

   ## Ejecución

   ```bash
   python pagina_principal.py
   ```

   ## Estructura del proyecto

   | Archivo | Descripción |
   |---|---|
   | `pagina_principal.py` | Ventana principal, menú y panel de inicio |
   | `paginas/productos.py` | Gestión de productos |
   | `paginas/categorias.py` | Gestión de categorías |
   | `paginas/movimientos.py` | Entradas y salidas de inventario |
   | `paginas/alerta.py` | Productos con stock bajo |
   | `paginas/report.py` | Reportes, exportación a PDF e impresión |
   | `paginas/conexion.py` | Conexión a MySQL (lee los datos de `.env`) |
   | `hilo/hilo.py` | Carga de datos en segundo plano (threads) |
   | `estilos/estilos.py` | Estilos visuales de la interfaz |
   | `probar_conexion.py` | Comprueba la conexión a la base de datos |

## Ramas

- `main`: versión estable, lista para ejecutar.
- `develop`: desarrollo y pruebas de nuevas funciones.
