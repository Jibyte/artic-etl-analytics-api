# Documentación Técnica y Especificación de Arquitectura — `artic-etl-analytics-api`

## 1. Descripción General del Sistema

`artic-etl-analytics-api` es un servicio backend de Ingeniería de Datos desarrollado en **FastAPI** bajo el patrón arquitectónico **MVC + Services**. Su objetivo es orquestar un pipeline **ETL (Extract, Transform, Load)** completo y exponer endpoints de análisis estadístico y auditoría cruzada sobre la colección pública de obras de arte del **Art Institute of Chicago** (`https://api.artic.edu/api/v1/artworks`).

### Stack Tecnológico
* **Framework Web / API REST:** FastAPI + Uvicorn
* **Base de Datos Staging (NoSQL):** MongoDB (`pymongo`)
* **Data Warehouse (SQL):** MySQL (`sqlalchemy` + `pymysql`)
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

### Alexander: Núcleo de Infraestructura, Modelado SQL, Extracción (Fase E) y Perfil Dual

* **Ramas sugeridas:** `feature/core-setup`, `feature/models-schemas`, `feature/etl-extract`, `feature/analitica-perfil-dual`
* **Archivos asignados:**
  * `requirements.txt`, `.env.example`
  * `app/config.py`
  * `app/database.py`
  * `app/main.py`
  * `app/models/entidad_sql.py`
  * `app/views/schemas.py`
  * `app/services/etl_service.py` (función de extracción)
  * `app/controllers/etl_controller.py` (endpoint `POST /api/v1/etl/extraer`)
  * `app/services/analitica_service.py`
  * `app/controllers/analitica_controller.py`

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

5. **Endpoint de Perfil Dual (`GET /api/v1/analitica/perfil/{id}` en `feature/analitica-perfil-dual`):**
   * Consultar simultáneamente el documento crudo en MongoDB (`_id = id`) y el registro limpio en MySQL (`id = id`).
   * Manejar los **3 escenarios obligatorios**: existe en ambas bases (`200 OK` con `vista_mongo` y `vista_sql`), existe solo en una (`200 OK` con la vista disponible, la faltante en `null` y campo `warning`), o no existe en ninguna (`404 Not Found`).

---

### Salomé: Transformación Pandas, Carga Data Warehouse y Reset (Fases T, L y Reset)

* **Ramas sugeridas:** `feature/etl-transform-load`, `feature/etl-reset-truncate`
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

### Integrante 3: Motor de Analítica Estadística Dinámica

* **Ramas sugeridas:** `feature/analitica-columna`
* **Archivos asignados:**
  * `app/services/analitica_service.py`
  * `app/controllers/analitica_controller.py` (endpoints `GET /api/v1/analitica/columna/{nombre}`)

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

---

## 5. Registro Técnico de Implementación por Integrante

### Alexander: Núcleo de Infraestructura, Modelado SQL, Extracción (Fase E) y Perfil Dual

#### 1. Esquema Relacional Definitivo del Data Warehouse (`artworks_master`)

Definido mediante SQLAlchemy ORM en `app/models/entidad_sql.py` (clase `ArtworkMaster`). La tabla cuenta con **11 columnas tipadas** diseñadas para soportar los 5 perfiles estadísticos dinámicos del endpoint de analítica (`numérica`, `categórica`, `fecha`, `booleana` y `texto libre`):

| Columna | Tipo SQL | Nulabilidad | Origen / Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `INT` (PK) | `NOT NULL` | Clave primaria natural (`autoincrement=False`), alineada 1:1 con `_id` en MongoDB y `id` de la API. |
| `titulo` | `VARCHAR(255)` | `NOT NULL` | Título de la obra (`title`). |
| `artista` | `VARCHAR(255)` | `NULL` | Nombre del artista principal (`artist_title`). |
| `departamento` | `VARCHAR(150)` | `NULL` | Departamento curatorial (`department_title`). |
| `clasificacion` | `VARCHAR(150)` | `NULL` | Clasificación artística (`classification_title`). |
| `origen` | `VARCHAR(150)` | `NULL` | Lugar de origen de la obra (`place_of_origin`). |
| `anio_inicio` | `INT` | `NULL` | Año estimado de inicio de creación (`date_start`). |
| `anio_fin` | `INT` | `NULL` | Año estimado de finalización (`date_end`). |
| `es_dominio_publico` | `BOOLEAN` | `NULL` | Indicador de dominio público (`is_public_domain`), almacenado como `TINYINT(1)` en MySQL. |
| `fecha_actualizacion_api` | `DATE` | `NULL` | Fecha de última actualización en la fuente (`source_updated_at`). |
| `total_categorias` | `INT` | `NULL` | Atributo derivado: longitud del arreglo `category_titles`. |

#### 2. Implementación del Núcleo Base (`feature/core-setup`)

Componentes implementados y verificados para habilitar el desarrollo en paralelo de los tres integrantes:

* **Dependencias (`requirements.txt`):** Declaración de las 8 librerías base (`fastapi`, `uvicorn`, `pandas`, `pymongo`, `sqlalchemy`, `pymysql`, `requests`, `python-dotenv`).
* **Variables de Entorno (`app/config.py` y `.env.example`):** Centralización de configuraciones en la instancia única `settings` mediante `python-dotenv`, construyendo dinámicamente la propiedad `mysql_url` bajo el dialecto `mysql+pymysql://`.
* **Capa de Persistencia Dual (`app/database.py`):**
  * **MongoDB:** Instancia `mongo_client` (con `serverSelectionTimeoutMS=5000`), base de datos `artic_staging` y colección `artworks_raw` lista para importar.
  * **MySQL:** Motor `engine` con `pool_pre_ping=True`, fábrica de sesiones `SessionLocal`, clase declarativa `Base` y dependencia `get_db()` para inyección transaccional en FastAPI.
* **Contratos Pydantic (`app/views/schemas.py`):** Esquemas de validación `ExtraerRequest` (con restricción estricta `cantidad > 0`), `ExtraerResponse`, `TransformarResponse`, `ResetResponse` y `PerfilDualResponse` (con campos `vista_mongo`, `vista_sql` y `warning` opcionales).
* **Aplicación y Enrutadores (`app/main.py` y `controllers/`):** Inicialización de `FastAPI` con gestor de ciclo de vida `lifespan` que ejecuta `Base.metadata.create_all(bind=engine)` al arrancar, routers base montados bajo `/api/v1/etl` y `/api/v1/analitica`, y endpoint de verificación `GET /`.

#### 3. Decisiones Técnicas, Guía Multiplataforma (Linux / Windows) y Troubleshooting

* **Creación Autónoma de la Base de Datos en MySQL (`app/database.py`):**
  Antes de crear el motor definitivo hacia `artic_dw`, `app/database.py` ejecuta `ensure_mysql_database()`, conectándose temporalmente al servidor MySQL y lanzando:

  ```sql
  CREATE DATABASE IF NOT EXISTS `artic_dw` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  ```

  De este modo, ningún integrante necesita crear manualmente el esquema en DBeaver antes de iniciar la API, asegurando además compatibilidad total con caracteres especiales (`utf8mb4`).

* **Sustitución de `mysql-connector-python` por `pymysql`:**
  * **Incidencia:** En entornos con **Python 3.14**, `mysql-connector-python` falla al importarse con `AttributeError: module 'ssl' has no attribute 'PROTOCOL_TLSv1'`, debido a que Python 3.14 eliminó protocolos TLS 1.0 obsoletos aún referenciados internamente por dicho driver.
  * **Solución:** Se adoptó `pymysql` en `requirements.txt` y en las cadenas de conexión de `app/config.py` y `app/database.py` (`mysql+pymysql://`), garantizando compatibilidad entre versiones recientes de Python tanto en Linux como en Windows.

* **Guía de Puesta en Marcha para el Equipo (Linux y Windows):**
  1. **Crear y activar el entorno virtual:**
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
  2. **Instalar dependencias y configurar credenciales:**
     ```bash
     pip install -r requirements.txt
     ```
     Crear un archivo `.env` en la raíz copiando la estructura de `.env.example` y colocando la contraseña local de MySQL (`MYSQL_PASSWORD`).
  3. **Verificar que los servicios locales de MySQL y MongoDB estén activos:**
     * **Linux:**
       ```bash
       sudo systemctl start mysql mongod
       sudo systemctl is-active mysql mongod
       ```
     * **Windows:** Abrir la aplicación **Servicios** (`Win + R` → escribir `services.msc`) y confirmar que los servicios **MySQL** (ej. `MySQL80`) y **MongoDB Server** (`MongoDB`) estén en estado *En ejecución* (o iniciarlos desde PowerShell/CMD como Administrador con `net start MySQL80` y `net start MongoDB`).
  4. **Ejecutar el servidor de desarrollo FastAPI:**
     ```bash
     uvicorn app.main:app --reload
     ```
     Documentación interactiva disponible en `http://127.0.0.1:8000/docs`.

---

#### 4. Implementación de la Fase de Extracción (`feature/etl-extract`)

* **Servicio de Consumo Paginado e Ingesta Idempotente (`app/services/etl_service.py`):**
  * **`obtener_obras_api(cantidad: int)`:** Consulta `https://api.artic.edu/api/v1/artworks` gestionando paginación dinámica (`page` y `limit`, acotado a un máximo de `100` registros por petición mediante `min(100, restantes)`). Incluye encabezado `User-Agent` identificativo, control de corte seguro ante fin de páginas (`total_pages` o respuesta vacía) y captura de fallos de red o disponibilidad externa (`requests.RequestException`) respondiendo `HTTP 502 Bad Gateway`.
  * **`extraer_y_guardar_obras(cantidad: int)`:** Asigna explícitamente el identificador entero nativo de cada obra (`id`) como clave primaria documental `_id` en MongoDB (evitando el `ObjectId` autogenerado para garantizar cruce 1:1 con MySQL). Ejecuta escrituras atómicas idempotentes mediante:
    ```python
    artworks_collection.update_one(
        {"_id": documento["_id"]},
        {"$set": documento},
        upsert=True
    )
    ```
    Contabiliza `nuevos` (cuando `upserted_id is not None`) frente a `ya_existentes` en ejecuciones repetidas, y captura errores de persistencia (`PyMongoError`) devolviendo `HTTP 500`.

* **Controlador REST (`app/controllers/etl_controller.py`):**
  * Expone `POST /api/v1/etl/extraer` con código de respuesta `HTTP 201 Created`.
  * Valida automáticamente el cuerpo de entrada con `ExtraerRequest` (`cantidad > 0`, retornando `HTTP 422` ante valores inválidos) y serializa la salida con `ExtraerResponse`.

* **Nota de Coordinación para el Equipo (Entornos Locales):** Dado que MongoDB (`artic_staging`) y MySQL (`artic_dw`) operan en instancias locales independientes en el equipo de cada desarrollador, una vez que el **Integrante 2** integre estos cambios desde `main`, inicie sus servicios locales y configure su `.env`, deberá ejecutar primero `POST /api/v1/etl/extraer` localmente para poblar su colección `artworks_raw` antes de desarrollar y probar `POST /api/v1/etl/transformar`.

#### 5. Implementación de Auditoría Cruzada y Perfil Dual (`feature/analitica-perfil-dual`)

* **Servicio de Auditoría Dual (`app/services/analitica_service.py`):**
  * **`_sanitizar_documento_mongo(documento)`:** Convierte el documento retornado por PyMongo a diccionario estándar y serializa posibles instancias de `ObjectId` a `str`, manteniendo `_id` como entero (`int`).
  * **`_serializar_registro_sql(registro)`:** Transforma la instancia ORM `ArtworkMaster` en un diccionario con las 11 columnas del Data Warehouse, formateando `fecha_actualizacion_api` a cadena ISO (`YYYY-MM-DD`) cuando no es nula.
  * **`obtener_perfil_dual(obra_id: int, db: Session)`:** Ejecuta de forma independiente la búsqueda en MongoDB (`artworks_collection.find_one({"_id": obra_id})`) y en MySQL (`db.query(ArtworkMaster).filter(ArtworkMaster.id == obra_id).first()`), capturando fallos de conexión (`PyMongoError` / `SQLAlchemyError`) con `HTTP 500`. Implementa los 3 escenarios exigidos:
    1. **Ausente en ambas bases:** lanza `HTTP 404 Not Found`.
    2. **Presente solo en una base:** retorna `HTTP 200 OK` con la vista existente, la faltante en `None` (`null` en JSON) y el atributo `warning` detallando la inconsistencia de sincronización.
    3. **Presente en ambas bases:** retorna `HTTP 200 OK` con `id`, `vista_mongo`, `vista_sql` y `warning: null`.

* **Controlador REST (`app/controllers/analitica_controller.py`):**
  * Expone `GET /api/v1/analitica/perfil/{id}` validando el parámetro entero `id` en la ruta, inyectando la sesión transaccional de MySQL mediante `Depends(get_db)` y serializando la respuesta con `PerfilDualResponse`.

### Salomé: Transformación Pandas, Carga Data Warehouse y Reset (Fases T, L y Reset)

#### 1. Implementación de Transformación y Carga (`feature/etl-transform-load`)

**Endpoint:** `POST /api/v1/etl/transformar`

**Objetivo:** transformar los documentos crudos almacenados en MongoDB y cargarlos en la tabla relacional `artworks_master` de MySQL.

**Servicio de transformación (`app/services/etl_service.py`):**

- **Lectura de datos:** se recuperan los documentos de la colección `artworks_raw` mediante `artworks_collection.find({})`.
- **Transformación con Pandas:** se utiliza `pd.json_normalize()` para aplanar los documentos JSON.
- **Selección de atributos:** se mapean los campos necesarios al modelo `ArtworkMaster`, descartando los metadatos que no forman parte de la tabla SQL.
- **Limpieza de valores nulos:** los campos de texto vacíos se reemplazan por `"N/A"`; los valores numéricos y las fechas inválidas se conservan como `None`.
- **Conversión de tipos:** se normalizan fechas, enteros y valores booleanos antes de la carga.
- **Identificación:** se conserva el identificador `_id` de MongoDB como clave primaria `id` en MySQL.

**Carga idempotente en MySQL:**

Se utiliza SQLAlchemy con el dialecto MySQL y la instrucción `ON DUPLICATE KEY UPDATE`, que permite insertar registros nuevos y actualizar los existentes sin generar duplicados.

La tabla `artworks_master` se crea automáticamente al iniciar la aplicación mediante `Base.metadata.create_all(bind=engine)` si todavía no existe.

**Respuesta HTTP 200:**

```json
{
  "mensaje": "Pipeline finalizado",
  "registros_procesados": 50,
  "tabla_destino": "artworks_master",
  "status": 200
}
```

El campo `registros_procesados` representa la cantidad de registros nuevos insertados.

#### 2. Implementación del Reset (`feature/etl-reset-truncate`)

**Endpoint:** `DELETE /api/v1/etl/reset`

**Objetivo:** eliminar los datos del pipeline ETL en MongoDB y MySQL, conservando la estructura de la base de datos relacional.

**Procedimiento:**

1. Se consulta la cantidad de filas existentes en `artworks_master`.
2. Se ejecuta `TRUNCATE TABLE artworks_master` para vaciar MySQL sin eliminar la tabla ni su clave primaria.
3. Se utiliza `artworks_collection.delete_many({})` para eliminar los documentos de MongoDB.
4. Se devuelve un resumen de los registros eliminados.

**Respuesta HTTP 200 obtenida durante las pruebas:**

```json
{
  "mensaje": "Sistema reseteado correctamente",
  "mongo_docs_eliminados": 10,
  "mysql_rows_eliminadas": 10,
  "status": 200
}
```

**Consideración técnica:** `TRUNCATE` realiza un commit implícito en MySQL. Por lo tanto, no puede revertirse mediante `rollback()` y la limpieza de MongoDB y MySQL no constituye una transacción atómica entre ambas bases.

#### 3. Pruebas y Validaciones

| Prueba | Resultado |
|---|---|
| Transformación de 50 documentos | Exitosa |
| Segunda ejecución sin insertar duplicados | Exitosa |
| Reset de 10 documentos en MongoDB | Exitoso |
| Reset de 10 filas en MySQL | Exitoso |
| Conservación de la tabla `artworks_master` | Verificada en DBeaver |
| Conservación de la clave primaria `id` | Verificada en DBeaver |
| Actualización de datos existentes mediante upsert | Pendiente de prueba específica |

**Herramientas utilizadas:** Swagger UI, MongoDB, MySQL y DBeaver.

#### 4. Archivos Modificados

- `app/services/etl_service.py`: implementación de las funciones `transformar_y_cargar_obras()` y `reset_pipeline()`.
- `app/controllers/etl_controller.py`: exposición de los endpoints REST y uso de la dependencia `get_db()`.

La implementación sigue la arquitectura **MVC + Services**, manteniendo separadas las responsabilidades del controlador, la lógica de transformación y la persistencia de datos.
---

### Integrante 3: Motor de Analítica Estadística Dinámica

*(Espacio reservado para documentar la implementación de /columna/{nombre} siguiendo la misma numeración interna 1, 2, 3...)*.