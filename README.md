# `artic-etl-analytics-api`

API REST desarrollada en **FastAPI** bajo el patrón arquitectónico **MVC + Services** que orquesta un pipeline **ETL (Extract, Transform, Load)** idempotente sobre la colección pública de obras de arte del **Art Institute of Chicago** (`https://api.artic.edu/api/v1/artworks`), integrando **MongoDB** como capa de Staging (NoSQL), **MySQL** como Data Warehouse relacional (SQL) y **Pandas** para transformación y análisis estadístico dinámico.

---

## Stack Tecnológico

* **Backend / API REST:** FastAPI + Uvicorn
* **Base de Datos Staging (NoSQL):** MongoDB (`pymongo`)
* **Data Warehouse (SQL):** MySQL (`sqlalchemy` + `pymysql`)
* **Procesamiento y Analítica:** Pandas
* **Validación de Contratos:** Pydantic
* **Configuración:** `python-dotenv`

---

## Estructura del Proyecto

```text
artic-etl-analytics-api/
├── .env.example                # Plantilla de variables de entorno requeridas
├── .gitignore                  # Exclusión de entorno virtual, .env y archivos temporales
├── requirements.txt            # Dependencias exactas del proyecto
├── README.md                   # Guía pública de instalación, uso y responsabilidades
├── documentacion.md            # Documentación técnica detallada y decisiones de ingeniería
└── app/
    ├── __init__.py
    ├── main.py                 # Punto de entrada FastAPI, ciclo de vida SQL y routers
    ├── config.py               # Carga centralizada de variables de entorno
    ├── database.py             # Gestión de conexiones a MongoDB y MySQL
    ├── controllers/
    │   ├── __init__.py
    │   ├── etl_controller.py       # Endpoints del pipeline (/extraer, /transformar, /reset)
    │   └── analitica_controller.py # Endpoints de analítica (/columna/{nombre}, /perfil/{id})
    ├── models/
    │   ├── __init__.py
    │   └── entidad_sql.py          # Modelo ORM SQLAlchemy de la tabla artworks_master
    ├── services/
    │   ├── __init__.py
    │   ├── etl_service.py          # Lógica de ingesta, transformación Pandas y carga SQL
    │   └── analitica_service.py    # Perfilado estadístico dinámico y auditoría dual
    └── views/
        ├── __init__.py
        └── schemas.py              # Esquemas Pydantic de validación Request/Response
```

---

## Instalación y Ejecución Local

### 1. Clonar el repositorio y crear el entorno virtual

```bash
git clone https://github.com/Jibyte/artic-etl-analytics-api
cd artic-etl-analytics-api
```

* **Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
* **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
* **Windows (CMD):**
  ```cmd
  python -m venv .venv
  .\.venv\Scripts\activate.bat
  ```

### 2. Instalar dependencias y configurar variables de entorno

```bash
pip install -r requirements.txt
```

Crea un archivo `.env` en la raíz del proyecto tomando como base `.env.example` y configura tus credenciales locales de MySQL (`MYSQL_USER` y `MYSQL_PASSWORD`). La base de datos `artic_dw` y la tabla `artworks_master` se crean automáticamente al iniciar la aplicación.

### 3. Verificar servicios locales de MySQL y MongoDB

* **Linux:**
  ```bash
  sudo systemctl start mysql mongod
  sudo systemctl is-active mysql mongod
  ```
* **Windows:** Confirmar desde **Servicios** (`services.msc`) que **MySQL** (`MySQL80`) y **MongoDB Server** (`MongoDB`) estén en estado *En ejecución*.

### 4. Iniciar el servidor FastAPI

```bash
uvicorn app.main:app --reload
```

La documentación interactiva Swagger UI estará disponible en `http://127.0.0.1:8000/docs`.

---

## Endpoints Implementados

### Pipeline ETL

#### `POST /api/v1/etl/extraer` *(Implementado por: Alexander)*
Extrae obras de arte desde la API del Art Institute of Chicago con paginación dinámica y las almacena de forma idempotente en MongoDB (`artic_staging.artworks_raw`) usando el `id` entero de la obra como `_id`.

* **Request Body (`application/json`):**
  ```json
  {
    "cantidad": 50
  }
  ```
* **Response (`201 Created`):**
  ```json
  {
    "mensaje": "Datos extraídos exitosamente",
    "nuevos": 50,
    "ya_existentes": 0,
    "fuente": "Art Institute of Chicago API",
    "status": 201
  }
  ```

#### `POST /api/v1/etl/transformar` *(Implementado por: Salomé)*

Transforma los documentos almacenados en MongoDB (`artic_staging.artworks_raw`) mediante **Pandas** y los carga en la tabla `artworks_master` de MySQL.

El proceso incluye aplanamiento de datos JSON, limpieza de valores nulos, conversión de tipos y selección de las columnas del modelo relacional.

La carga es **idempotente**: utiliza `INSERT ... ON DUPLICATE KEY UPDATE` para insertar obras nuevas y actualizar las existentes sin generar duplicados.

* **Request:** no requiere cuerpo JSON.
* **Response (`200 OK`):**

```json
{
  "mensaje": "Pipeline finalizado",
  "registros_procesados": 50,
  "tabla_destino": "artworks_master",
  "status": 200
}
```

El campo `registros_procesados` indica la cantidad de registros nuevos insertados durante la ejecución.

#### `DELETE /api/v1/etl/reset` *(Implementado por: Salomé)*

Permite reiniciar el pipeline ETL eliminando los documentos almacenados en MongoDB y vaciando la tabla `artworks_master` de MySQL.

Se utiliza `delete_many({})` para limpiar la colección de MongoDB y `TRUNCATE TABLE artworks_master` para vaciar MySQL, **conservando la tabla y su estructura**.

* **Request:** no requiere cuerpo JSON.
* **Response (`200 OK`):**

```json
{
  "mensaje": "Sistema reseteado correctamente",
  "mongo_docs_eliminados": 10,
  "mysql_rows_eliminadas": 10,
  "status": 200
}
```

Los campos `mongo_docs_eliminados` y `mysql_rows_eliminadas` indican cuántos registros fueron eliminados de cada base de datos.

**Nota:** el reset elimina los datos del pipeline, por lo que debe utilizarse únicamente cuando se necesite reiniciar el proceso.

### Analítica y Auditoría Dual

#### `GET /api/v1/analitica/columna/{nombre}` *(Implementado por: Daniela)*
Evalúa dinámicamente cualquier columna de la tabla `artworks_master` en MySQL (inspeccionando los metadatos de SQLAlchemy y los valores reales con Pandas, sin nombres de columnas hardcodeados) y retorna sus métricas estadísticas según el tipo detectado (`numerica`, `booleana`, `fecha`, `categorica` o `texto`). Si la columna no existe, responde `400 Bad Request` listando las columnas válidas.

* **Ejemplo de consulta (`GET /api/v1/analitica/columna/es_dominio_publico`):**
  ```json
  {
    "columna": "es_dominio_publico",
    "tipo": "booleana",
    "true": 32,
    "false": 18,
    "nulos": 0
  }

#### `GET /api/v1/analitica/perfil/{id}` *(Implementado por: Alexander)*
Consulta simultáneamente una obra de arte por su identificador entero tanto en MongoDB (`_id`) como en MySQL (`id`) para auditar la sincronización 1:1 del pipeline ETL.

* **Escenarios de respuesta:**
  * **Existe en ambas bases (`200 OK`):** Retorna `id`, `vista_mongo`, `vista_sql` y `"warning": null`.
  * **Existe solo en una base (`200 OK`):** Retorna la vista disponible, la faltante en `null` y un mensaje descriptivo en `warning`.
  * **No existe en ninguna base (`404 Not Found`):** Retorna detalle de registro no encontrado.

---

## División de Responsabilidades del Equipo

| Integrante | Rol y Módulo | Ramas Trabajadas | Entregables Principales |
| :--- | :--- | :--- | :--- |
| **Alexander** | **Infraestructura Base, Modelado SQL, Extracción (E) y Perfil Dual** | `feature/core-setup`<br>`feature/etl-extract`<br>`feature/analitica-perfil-dual` | Configuración `.env`, conexiones duales MongoDB/MySQL, modelo `ArtworkMaster` (11 columnas), esquemas Pydantic, `main.py`, extracción idempotente `POST /api/v1/etl/extraer` y auditoría cruzada `GET /api/v1/analitica/perfil/{id}`. |
| **Salomé** | **Transformación Pandas, Carga DW (TL) y Reset** | *Por registrar* | Limpieza y aplanamiento con Pandas, carga idempotente en MySQL (`POST /api/v1/etl/transformar`) y vaciado controlado (`DELETE /api/v1/etl/reset`). |
| **Daniela** | **Analítica Estadística Dinámica** | `feature/analitica-columna` | Perfilado estadístico dinámico por tipo de columna (`GET /api/v1/analitica/columna/{nombre}`) sin hardcodear nombres de columnas. |