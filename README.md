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

#### `POST /api/v1/etl/extraer`
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

*(Sección reservada para documentar `POST /api/v1/etl/transformar` y `DELETE /api/v1/etl/reset` — Integrante 2).*

### Analítica y Auditoría Dual

*(Sección reservada para documentar `GET /api/v1/analitica/columna/{nombre}` y `GET /api/v1/analitica/perfil/{id}` — Integrante 3).*

---

## División de Responsabilidades del Equipo

| Integrante | Rol y Módulo | Ramas Trabajadas | Entregables Principales |
| :--- | :--- | :--- | :--- |
| **Alexander** | **Infraestructura Base, Modelado SQL y Extracción (Fase E)** | `feature/core-setup`<br>`feature/etl-extract` | Configuración `.env`, conexiones duales MongoDB/MySQL, modelo `ArtworkMaster` (11 columnas), esquemas Pydantic, `main.py` y endpoint idempotente `POST /api/v1/etl/extraer`. |
| **Integrante 2** | **Transformación Pandas, Carga DW (TL) y Reset** | *Por registrar* | Limpieza y aplanamiento con Pandas, carga idempotente en MySQL (`POST /api/v1/etl/transformar`) y vaciado controlado (`DELETE /api/v1/etl/reset`). |
| **Integrante 3** | **Analítica Dinámica y Perfil Dual** | *Por registrar* | Perfilado estadístico dinámico por tipo de columna (`GET /api/v1/analitica/columna/{nombre}`) y auditoría cruzada Mongo/SQL (`GET /api/v1/analitica/perfil/{id}`). |