# Documentación Técnica y Especificación de Arquitectura — `artic-etl-analytics-api`

## 1. Descripción General del Sistema

`artic-etl-analytics-api` es un servicio backend de Ingeniería de Datos desarrollado en **FastAPI** bajo el patrón arquitectónico **MVC + Services**. Su objetivo es orquestar un pipeline **ETL (Extract, Transform, Load)** completo y exponer endpoints de análisis estadístico y auditoría cruzada sobre la colección pública de obras de arte del **Art Institute of Chicago** (`https://api.artic.edu/api/v1/artworks`).

### Stack Tecnológico
* **Framework Web / API REST:** FastAPI + Uvicorn
* **Base de Datos Staging (NoSQL):** MongoDB (`pymongo`)
* **Data Warehouse (SQL):** MySQL (`sqlalchemy` + `mysql-connector-python`)
* **Procesamiento y Perfilado de Datos:** Pandas
* **Validación de Contratos:** Pydantic
* **Gestión de Configuración:** `python-dotenv`

---

## 2. Arquitectura del Pipeline de Datos

El flujo de información atraviesa tres etapas desacopladas:

1. **Fuente Externa (Source):** API REST pública del Art Institute of Chicago (`GET https://api.artic.edu/api/v1/artworks`), consumida mediante paginación dinámica (`page` y `limit`). Entidad única: **Obras de Arte (`artworks`)**.
2. **Capa de Staging (NoSQL - MongoDB):** Almacena el documento JSON crudo tal como proviene de la API. Utiliza el identificador entero nativo de la obra (`id`) como clave primaria documental (`_id`) para garantizar idempotencia y trazabilidad directa.
3. **Data Warehouse (SQL - MySQL):** Tabla relacional plana única (`artworks_master`) con mínimo 8 columnas tipadas (`INT`, `VARCHAR`, `FLOAT`, `DATE`, `BOOLEAN`). Los datos son aplanados, normalizados y limpiados mediante Pandas e insertados mediante SQLAlchemy manteniendo alineada la clave primaria (`id`) con el `_id` de MongoDB.

---

## 3. Estructura de Directorios del Repositorio

    artic-etl-analytics-api/
    ├── .env                        # Variables de entorno locales (excluido del control de versiones)
    ├── .env.example                # Plantilla estándar de variables de entorno requeridas
    ├── .gitignore                  # Exclusión de entorno virtual, credenciales y cachés
    ├── requirements.txt            # Dependencias exactas del proyecto
    ├── README.md                   # Documentación pública de instalación, uso y equipo
    ├── documentacion.md            # Especificación técnica del sistema y asignación de roles
    └── app/
        ├── __init__.py
        ├── main.py                 # Instancia principal FastAPI, eventos de inicio y routers
        ├── config.py               # Lectura centralizada de variables de entorno
        ├── database.py             # Gestión de conexiones a MongoDB y motor/sesión MySQL
        ├── controllers/
        │   ├── __init__.py
        │   ├── etl_controller.py       # Rutas REST del pipeline (/extraer, /transformar, /reset)
        │   └── analitica_controller.py # Rutas REST de analítica (/columna/{nombre}, /perfil/{id})
        ├── models/
        │   ├── __init__.py
        │   └── entidad_sql.py          # Modelo ORM SQLAlchemy de la tabla artworks_master
        ├── services/
        │   ├── __init__.py
        │   ├── etl_service.py          # Lógica de negocio de ingesta, transformación Pandas y carga SQL
        │   └── analitica_service.py    # Motor estadístico dinámico y auditoría dual Mongo/SQL
        └── views/
            ├── __init__.py
            └── schemas.py              # Esquemas Pydantic de validación de entrada y salida

---

## 4. Asignación Detallada de Responsabilidades por Integrante

Para cumplir con las reglas de ingeniería colaborativa del proyecto, **no se permiten commits directos a `main`**. Cada integrante debe desarrollar sus entregables en ramas `feature/...`, alcanzar un mínimo de **10 commits atómicos y descriptivos**, e integrar su trabajo mediante **Pull Requests** revisados hacia `main`.

> **Nota de Sustentación:** Aunque el desarrollo se divide en tres módulos para maximizar la productividad en paralelo, los tres integrantes deben dominar el funcionamiento integral del código (Controllers, Services, Models y consultas SQL/MongoDB).

---

### Integrante 1: Núcleo de Infraestructura, Modelado de Datos y Extracción (Fase E)

* **Ramas sugeridas:** `feature/core-setup`, `feature/models-schemas`, `feature/etl-extract`
* **Archivos asignados:**
  * `requirements.txt`, `.env.example`
  * `app/config.py`
  * `app/database.py`
  * `app/main.py`
  * `app/models/entidad_sql.py`
  * `app/views/schemas.py`
  * `app/services/etl_service.py` (función de extracción)
  * `app/controllers/etl_controller.py` (endpoint `POST /api/v1/etl/extraer`)

#### Tareas Técnicas Específicas:
1. **Configuración y Conexiones (`config.py`, `database.py`, `main.py`):**
   * Centralizar la carga de credenciales de MongoDB, MySQL y URL base de la API mediante `python-dotenv`.
   * Implementar el cliente de MongoDB (PyMongo) y el `engine` / `SessionLocal` / `Base` de SQLAlchemy para MySQL.
   * Configurar `app/main.py` registrando los routers de ETL y Analítica bajo el prefijo `/api/v1` y asegurando la creación automática de tablas (`Base.metadata.create_all`) al iniciar.
2. **Modelado Relacional (`app/models/entidad_sql.py`):**
   * Definir la tabla plana `artworks_master` con clave primaria explícita `id` (`Integer`, `primary_key=True`, `autoincrement=False`) alineada con el ID de la API.
   * Incluir al menos **8 columnas significativas** con tipos estrictos (`VARCHAR`, `INT`, `FLOAT`, `DATE`, `BOOLEAN`), incluyendo campos extraídos y derivados de la obra de arte (título, artista, fecha de inicio/fin, medio/técnica, departamento, origen, clasificación, dominio público, etc.).
3. **Esquemas de Validación (`app/views/schemas.py`):**
   * Definir los modelos Pydantic para validar la entrada (`cantidad > 0` en `/extraer`) y estructurar las respuestas JSON de todos los endpoints (`201 Created`, `200 OK`, errores `400` y `404`).
4. **Endpoint de Extracción (`POST /api/v1/etl/extraer`):**
   * Consumir `https://api.artic.edu/api/v1/artworks` manejando paginación (`page` y `limit`) hasta completar la `cantidad` solicitada.
   * Asignar el `id` entero de cada obra como `_id` en MongoDB (prohibido el `ObjectId` autogenerado).
   * Garantizar **idempotencia** mediante verificación previa o `upsert`, retornando HTTP `201` con el conteo exacto de documentos `nuevos` y `ya_existentes`.

---

### Integrante 2: Transformación Pandas, Carga Data Warehouse y Reset (Fases T, L y Reset)

* **Ramas sugeridas:** `feature/etl-transform-load`, `feature/etl-reset`
* **Archivos asignados:**
  * `app/services/etl_service.py` (funciones de transformación, carga y reset)
  * `app/controllers/etl_controller.py` (endpoints `POST /api/v1/etl/transformar` y `DELETE /api/v1/etl/reset`)

#### Tareas Técnicas Específicas:
1. **Extracción desde Staging y Transformación con Pandas (`POST /api/v1/etl/transformar`):**
   * Leer todos los documentos crudos almacenados en la colección de MongoDB.
   * Aplanar estructuras JSON anidadas y seleccionar/mapear las columnas definidas en `entidad_sql.py` (descartando metadatos irrelevantes de la API).
   * Aplicar reglas estrictas de limpieza de nulos:
     * Columnas de **texto categórico**: imputar valores nulos o vacíos con `"N/A"`.
     * Columnas **numéricas y de fecha**: preservar `NULL` (`None` en Python/MySQL) para evitar sesgos estadísticos en promedios, medianas y rangos temporales.
   * Garantizar tipado consistente (conversión de fechas, booleanos y enteros/flotantes) antes de la inserción.
2. **Carga Idempotente en MySQL (`Load`):**
   * Verificar existencia de la tabla mediante `Base.metadata.create_all(bind=engine)` sin utilizar nunca `df.to_sql(..., if_exists="replace")`.
   * Ejecutar inserción/actualización idempotente (`INSERT ... ON DUPLICATE KEY UPDATE` vía dialecto MySQL de SQLAlchemy) usando el `id` alineado con el `_id` de MongoDB, evitando duplicados en ejecuciones repetidas.
   * Retornar HTTP `200` con el total de `registros_procesados` y el nombre de `tabla_destino`.
3. **Limpieza Total del Sistema (`DELETE /api/v1/etl/reset`):**
   * Eliminar todos los documentos de la colección en MongoDB (`delete_many({})`) contabilizando los registros borrados.
   * Vaciar la tabla `artworks_master` en MySQL ejecutando `TRUNCATE TABLE artworks_master` (prohibido usar `DROP TABLE`) contabilizando las filas eliminadas previamente.
   * Retornar HTTP `200` con `mongo_docs_eliminados` y `mysql_rows_eliminadas`.

---

### Integrante 3: Motor de Analítica Dinámica y Auditoría Dual (Endpoints Analíticos)

* **Ramas sugeridas:** `feature/analitica-columna`, `feature/analitica-perfil-dual`
* **Archivos asignados:**
  * `app/services/analitica_service.py`
  * `app/controllers/analitica_controller.py` (endpoints `GET /api/v1/analitica/columna/{nombre}` y `GET /api/v1/analitica/perfil/{id}`)

#### Tareas Técnicas Específicas:
1. **Análisis Estadístico Dinámico por Columna (`GET /api/v1/analitica/columna/{nombre}`):**
   * Consultar los metadatos de la tabla `artworks_master` en MySQL. Si `{nombre}` no existe, responder HTTP `400 Bad Request` listando las columnas válidas.
   * Detectar el tipo de dato **de forma 100% dinámica** inspeccionando los tipos de columna de SQLAlchemy / `dtypes` de Pandas (prohibido hardcodear nombres de columnas).
   * Implementar los **5 perfiles de salida requeridos**:
     * **Booleana** (columnas `BOOLEAN` / `TINYINT(1)` con valores `0` y `1`): conteo de `true`, `false` y `nulos`.
     * **Numérica** (`INT`, `FLOAT`): `min`, `max`, `promedio`, `mediana`, `desviacion_std` y `nulos`.
     * **Fecha** (`DATE`, `DATETIME`): `min`, `max`, `rango_dias` y `nulos`.
     * **Categórica** (texto con valores repetidos): `valores_unicos`, `distribucion` (frecuencias), `valor_mas_comun` y `nulos`.
     * **Texto libre** (texto donde todos los valores no nulos son únicos): `valores_unicos` y `nulos`.
2. **Auditoría Cruzada MongoDB + MySQL (`GET /api/v1/analitica/perfil/{id}`):**
   * Consultar simultáneamente el documento en MongoDB (`_id = id`) y el registro en MySQL (`id = id`).
   * Manejar los **3 escenarios obligatorios**:
     * **Existe en ambas bases:** retornar HTTP `200 OK` con `id`, `vista_mongo` y `vista_sql`.
     * **Existe solo en una base:** retornar HTTP `200 OK` con la vista disponible, la faltante en `null` y un campo `warning` explicando la inconsistencia de sincronización.
     * **No existe en ninguna base:** retornar HTTP `404 Not Found`.