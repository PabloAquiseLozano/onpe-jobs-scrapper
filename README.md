# ONPE Convocatorias Scraper

Scraper automatizado para extraer todas las convocatorias laborales publicadas en la plataforma **SIGLOC** (Sistema Integrado de Gestión de Locadores de Servicios) de la ONPE.

El sitio `reclutamiento.onpe.gob.pe` está protegido por **Cloudflare**, lo que bloquea peticiones directas con `requests`, `curl` o bots convencionales. Este scraper utiliza [`nodriver`](https://github.com/ultrafunkamsterdam/nodriver) (sucesor de `undetected-chromedriver`) para superar la protección de Cloudflare y consumir la API interna del frontend.

## Arquitectura

```
Public-Job-Scrapper/
├── schedule-task/              # Backend: Scraper + Cron job
│   ├── main.py                 # Entry point (ejecución única o programada)
│   ├── config.py               # Configuración (URL, Chrome, intervalos, credenciales)
│   ├── requirements.txt        # Dependencias Python
│   ├── schema.sql              # Esquema SQL para Supabase
│   ├── .env.example            # Plantilla de variables de entorno
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── base_scraper.py     # Clase base (upsert a Supabase)
│   │   └── onpe_scraper.py     # Scraper ONPE con nodriver
│   ├── database/
│   │   ├── __init__.py
│   │   └── supabase_client.py  # Cliente Supabase + operaciones CRUD
│   └── .github/workflows/
│       └── scraper.yml         # GitHub Actions (cron cada hora → scraper → Supabase)
├── frontend/                   # Frontend estático (consulta Supabase directamente)
│   ├── index.html
│   ├── styles.css
│   └── app.js                  # Usa @supabase/supabase-js vía CDN
├── README.md
└── .gitignore
```

## Flujo de datos

1. **Cron Job** (`schedule-task/main.py` via GitHub Actions o cron del sistema)
   - Lanza Chrome headless con `nodriver`
   - Supera Cloudflare y llama a la API interna de ONPE
   - Obtiene todas las convocatorias en JSON

2. **Base de datos** (`schedule-task/database/supabase_client.py`)
   - Hace `upsert` en tabla `convocatorias` de Supabase (clave única: `id_perfil`)
   - Solo necesita `SUPABASE_SERVICE_ROLE_KEY` (escritura)

3. **Frontend** (`frontend/`)
   - HTML/CSS/JS estático, sin build, sin backend propio
   - Usa `@supabase/supabase-js` (CDN) con `SUPABASE_ANON_KEY` (lectura)
   - Consulta Supabase directamente: paginación, filtros, búsqueda full-text

> **No hay API intermedia**. El frontend habla directo con Supabase.

## Datos obtenidos

| Campo | Descripción |
|---|---|
| `id_perfil` | Identificador del perfil en SIGLOC |
| `titulo` | Nombre del puesto |
| `denominacion` | Denominación oficial del cargo |
| `categoria` | Categoría del perfil (si aplica) |
| `rubros` | Lista de rubros (Informática, Finanzas, etc.) |
| `remuneracion_soles` | Remuneración mensual en soles |
| `cantidad_requerida` | Vacantes disponibles |
| `fecha_publicacion` | Fecha y hora de publicación |
| `id_proceso_electoral` | Proceso electoral asociado |
| `tipo_perfil` | Tipo de perfil |
| `estado_perfil` | Estado (0 = vigente, 1 = concluido) |
| `url_lista` | URL de la lista de convocatorias |
| `url_postulacion` | URL para postular (requiere login) |
| `url_detalle` | URL directa a la convocatoria |
| `scraped_at` | Timestamp de extracción |

## Instalación

### Prerrequisitos

- Python 3.10+
- Google Chrome o Chromium instalado en el sistema
- Proyecto en [Supabase](https://supabase.com)

### Setup (scraper)

```bash
git clone https://github.com/<tu-usuario>/Public-Job-Scrapper.git
cd Public-Job-Scrapper/schedule-task

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configuración de Supabase

1. Crea un proyecto en [Supabase](https://supabase.com)
2. Ejecuta `schema.sql` en el **SQL Editor** de Supabase
3. Copia `.env.example` a `.env` y completa credenciales:

```bash
cp .env.example .env
# Edita .env
```

**Credenciales en `.env` (schedule-task/):**
- `SUPABASE_URL` — URL del proyecto (ej: `https://abc123.supabase.co`)
- `SUPABASE_SERVICE_ROLE_KEY` — Clave `service_role` secreta (para escritura del scraper)

**Credenciales en `frontend/app.js`:**
- `SUPABASE_URL` — misma URL
- `SUPABASE_ANON_KEY` — Clave `anon` pública (para lectura del frontend)

> **Seguridad:** `service_role_key` **solo** en scraper (GitHub Actions secrets o servidor). Nunca en frontend.

## Uso

### Scraper (extrae datos y guarda en Supabase)

```bash
cd schedule-task

# Ejecución única
python main.py

# Ejecución programada (cada 4.8 horas, configurable en config.py)
python main.py --schedule
```

### Frontend (consulta Supabase directamente)

```bash
# Opción 1: Servir estático simple
cd ../frontend
python -m http.server 3000
# Abre http://localhost:3000

# Opción 2: Cualquier servidor estático (nginx, Apache, Vercel, Netlify, GitHub Pages)
# Solo sirve la carpeta frontend/
```

Verás:
- Listado de convocatorias con filtros (búsqueda por título, estado vigente/concluido)
- Paginación
- Cards con título, denominación, rubros, remuneración, estado, enlaces a detalle/postulación
- Estadísticas globales (total, vigentes, concluidas)

### Automatización con GitHub Actions (recomendado)

El workflow en `schedule-task/.github/workflows/scraper.yml`:

- Ejecuta el scraper **cada hora** (`cron: "0 * * * *"`)
- Se puede ejecutar manualmente (`workflow_dispatch`)
- Instala Chrome y dependencias automáticamente
- Hace `upsert` en Supabase

**Configura en GitHub (Settings → Secrets and variables → Actions):**

| Secret | Valor |
|---|---|
| `SUPABASE_URL` | `https://tu-proyecto.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | `tu-service-role-key` |

> No necesitas `SUPABASE_ANON_KEY` en GitHub Actions; solo se usa en el frontend.

### Despliegue del Frontend

El frontend es **100% estático** (HTML/CSS/JS). Despliega en cualquier hosting estático:

- **Vercel/Netlify**: Conecta repo, build command vacío, output dir `frontend/`
- **GitHub Pages**: Push `frontend/` a branch `gh-pages` o usa action
- **nginx/Apache/VPS**: Sirve carpeta `frontend/` como estático
- **Cloudflare Pages / AWS S3 + CloudFront / Firebase Hosting**

Solo edita `frontend/app.js` y pon tus `SUPABASE_URL` y `SUPABASE_ANON_KEY` (o usa variables de entorno en tu hosting).

## Estructura de la tabla en Supabase

```sql
convocatorias (
    id SERIAL PRIMARY KEY,
    id_perfil INTEGER UNIQUE,
    titulo TEXT,
    denominacion TEXT,
    categoria TEXT,
    rubros TEXT[],
    remuneracion_soles NUMERIC(10, 2),
    cantidad_requerida INTEGER,
    fecha_publicacion TEXT,
    id_proceso_electoral INTEGER,
    tipo_perfil TEXT,
    estado_perfil INTEGER,
    estado_postulacion TEXT,
    postulacion_habilitada BOOLEAN,
    url_lista TEXT,
    url_postulacion TEXT,
    url_detalle TEXT,
    scraped_at TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
)
```

Índices:
- `fecha_publicacion` — ordenamiento
- `estado_perfil` — filtro vigentes/concluidas
- `remuneracion_soles` — filtros de salario
- `to_tsvector('spanish', titulo)` — búsqueda full-text

## Sobre la API interna de ONPE

La API `/sigloc-backend/v1/api/convocatoria/lista` no es pública ni documentada. Fue descubierta mediante ingeniería inversa del frontend Angular de la plataforma SIGLOC.

- URL base en environment de Angular: `apiUrl: "/sigloc-backend"`
- Endpoint: `POST /v1/api/convocatoria/lista`
- Tipos: **Locación de Servicios** (tipo 1) y **Concurso Público** (tipo 2)

## Licencia

MIT