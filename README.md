# ONPE Convocatorias Scraper

Scraper automatizado para extraer todas las convocatorias laborales publicadas en la plataforma **SIGLOC** (Sistema Integrado de Gestión de Locadores de Servicios) de la ONPE.

El sitio `reclutamiento.onpe.gob.pe` está protegido por **Cloudflare**, lo que bloquea peticiones directas con `requests`, `curl` o bots convencionales. Este scraper utiliza [`nodriver`](https://github.com/ultrafunkamsterdam/nodriver) (sucesor de `undetected-chromedriver`) para superar la protección de Cloudflare y consumir la API interna del frontend.

## Datos obtenidos

Cada convocatoria incluye:

| Campo | Descripcion |
|---|---|
| `id` | Identificador del perfil en SIGLOC |
| `titulo` | Nombre del puesto |
| `denominacion` | Denominacion oficial del cargo |
| `categoria` | Categoria del perfil (si aplica) |
| `rubros` | Lista de rubros asignados (Informatica, Finanzas, etc.) |
| `remuneracion_soles` | Remuneracion mensual en soles |
| `cantidad_requerida` | Vacantes disponibles |
| `fecha_publicacion` | Fecha y hora de publicacion |
| `id_proceso_electoral` | Proceso electoral asociado |
| `tipo_perfil` | Tipo de perfil |
| `estado_perfil` | Estado (0 = vigente, 1 = concluido) |
| `url_lista` | URL de la lista de convocatorias |
| `url_postulacion` | URL para postular (requiere login) |
| `url_detalle` | URL directa a la convocatoria |
| `scraped_at` | Timestamp de extraccion |

## Arquitectura

```
Public-Job-Scrapper/
├── config.py                # Configuracion (URL, Chrome, intervalos)
├── main.py                  # Entry point (ejecucion unica o programada)
├── requirements.txt
├── .github/workflows/
│   └── scraper.yml          # GitHub Actions (cron cada hora)
├── scraper/
│   ├── __init__.py
│   ├── base_scraper.py      # Clase base (guardado JSON)
│   └── onpe_scraper.py      # Scraper ONPE con nodriver
├── data/                    # Output JSON (commiteado por el bot)
│   └── ONPE_2026-07-30.json
└── README.md
```

### Como funciona

1. **Lanza Chrome en modo headless** via `nodriver` con flags anti-deteccion (`--headless=new`, `--disable-blink-features=AutomationControlled`).
2. **Navega a `reclutamiento.onpe.gob.pe/convocatorias`** y espera a que Cloudflare resuelva el challenge. Si el titulo de la pagina sigue siendo el challenge `Just a moment`, aborta la corrida; cualquier otro titulo (como el oficial de la ONPE) se considera superado.
3. **Llama a la API interna** desde el contexto del navegador (con cookies y tokens de Cloudflare ya resueltos):

   ```
   POST /sigloc-backend/v1/api/convocatoria/lista
   Content-Type: application/json
   {
     "tipoConvocatoria": 1,      # 1=LocacionServicio, 2=ConcursoPublico
     "idRubro": 0,
     "idDepartamento": 0,
     "verConcluidas": false,
     "palabraClave": null,
     "idOdp": null,
     "idLugarEjecucion": 0,
     "fechaPublicacion": {"start": null, "end": null},
     "page": 0,
     "pageSize": 100
   }
   ```

4. **Pagina automaticamente** hasta obtener todas las convocatorias (vigentes y concluidas).
5. **Normaliza y deduplica** los resultados.
6. **Guarda** en `data/ONPE_YYYY-MM-DD.json`.

## Instalacion

### Prerrequisitos

- Python 3.10+
- Google Chrome o Chromium instalado en el sistema

### Setup

```bash
git clone https://github.com/<tu-usuario>/Public-Job-Scrapper.git
cd Public-Job-Scrapper

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

## Uso

### Ejecucion unica (local)

```bash
python main.py
```

### Ejecucion programada (local)

```bash
python main.py --schedule
```

Ejecuta el scraping cada 4.8 horas (configurable en `config.py`).

### Automatizacion con GitHub Actions

El repositorio incluye un workflow en `.github/workflows/scraper.yml` que:

- Ejecuta el scraper **cada hora** automaticamente (`cron: "0 * * * *"`).
- Tambien se puede ejecutar manualmente desde la pestana **Actions** en GitHub (`workflow_dispatch`).
- Instala Google Chrome y las dependencias automatically.
- Usa `actions/checkout@v5` y `actions/setup-python@v6` (runtime Node.js 24), libres de los warnings de deprecacion de Node.js 20.
- **Commitea el JSON** resultante al repositorio, para que los datos queden visibles y versionados.

**Costo en GitHub Actions (repositorio publico):**

| Concepto | Calculo | |
|---|---|---|
| Frecuencia | Cada hora | 24 corridas/dia |
| Duracion por corrida | ~1 min | |
| Minutos/mes | ~720 | |
| Limite gratuito | 2,000 | |
| Uso | ~36% | Dentro del free tier |

No requiere configurar ningun secret. GitHub Actions inyecta `GITHUB_TOKEN` automaticamente.

### Configuracion

Editar `config.py`:

```python
ONPE = {
    "name": "ONPE",
    "base_url": "https://reclutamiento.onpe.gob.pe/convocatorias",
    "chrome_path": "/usr/bin/google-chrome-stable",  # Ruta a Chrome
    "cf_wait": 20,  # Segundos a esperar por Cloudflare
    "headless": True,  # True para CI/servidores, False para debug local
}

SCRAPE_INTERVAL_HOURS = 4.8  # Intervalo del modo --schedule local
```

## Output

```bash
$ python main.py

[2026-07-30T16:28:02] Scraping ONPE...
  Concluidas LocacionServicio pagina 0: 100 registros (total 203, paginas 3)
  Concluidas LocacionServicio pagina 1: 100 registros (total 203, paginas 3)
  Concluidas LocacionServicio pagina 2: 3 registros (total 203, paginas 3)
  Concluidas ConcursoPublico pagina 0: 6 registros (total 6, paginas 1)
  -> 209 convocatorias guardadas en data/ONPE_2026-07-30.json
```

### Ejemplo de salida JSON

```json
{
  "id": 8497,
  "titulo": "AUXILIAR TECNICO NOCTURNO DE ODPE",
  "rubros": ["Atencion al Ciudadano y Soporte Electoral"],
  "remuneracion_soles": 1800.0,
  "fecha_publicacion": "2026-07-27T19:19:27.937622",
  "url_lista": "https://reclutamiento.onpe.gob.pe/convocatorias",
  "url_postulacion": "https://reclutamiento.onpe.gob.pe/login",
  "url_detalle": "https://reclutamiento.onpe.gob.pe/convocatorias?perfil=8497&proceso=70"
}
```

## Sobre la API

La API `/sigloc-backend/v1/api/convocatoria/lista` no es publica ni documentada. Fue descubierta mediante ingenieria inversa del frontend Angular de la plataforma SIGLOC, inspeccionando el codigo fuente de los bundles JS (`main-*.js` y `chunk-*.js`).

- La URL base se define en el environment de Angular como `apiUrl: "/sigloc-backend"`
- El servicio `ConvocatoriaService` construye el endpoint completo como `POST /v1/api/convocatoria/lista`
- Las convocatorias se dividen en dos tipos: **Locacion de Servicios** (tipo 1) y **Concurso Publico** (tipo 2)

## Licencia

MIT
