import asyncio
import json
from datetime import datetime
from typing import Any

import nodriver as uc

from scraper.base_scraper import BaseScraper

BASE_URL = "https://reclutamiento.onpe.gob.pe"
CONVOCATORIAS_URL = f"{BASE_URL}/convocatorias"
API_PREFIX = "/sigloc-backend/v1/api"

CF_WAIT_SECONDS = 20
PAGE_SIZE = 100

TIPO_LOCACION_SERVICIO = 1
TIPO_CONCURSO_PUBLICO = 2

CF_TITULO_BLOCKED = "Just a moment"


def _build_filter(
    tipo_convocatoria: int,
    ver_concluidas: bool = False,
    page: int = 0,
    page_size: int = PAGE_SIZE,
) -> str:
    return json.dumps(
        {
            "tipoConvocatoria": tipo_convocatoria,
            "idRubro": 0,
            "idDepartamento": 0,
            "verConcluidas": ver_concluidas,
            "palabraClave": None,
            "idOdp": None,
            "idLugarEjecucion": 0,
            "fechaPublicacion": {"start": None, "end": None},
            "page": page,
            "pageSize": page_size,
        },
        separators=(",", ":"),
    )


def _build_post_body(payload: str) -> str:
    return (
        "fetch('"
        + API_PREFIX
        + "/convocatoria/lista',"
        + "{method:'POST',headers:{'Content-Type':'application/json'},"
        + "body:'"
        + payload.replace("'", "\\'")
        + "'}"
        + ").then(r=>r.text().then(t=>r.status+':'+t))"
    )


def _build_get_body(endpoint: str) -> str:
    return (
        f"fetch('{API_PREFIX}/{endpoint}')"
        ".then(r=>r.text().then(t=>r.status+':'+t))"
    )


def _parse_api_response(raw: str) -> dict[str, Any] | None:
    if not raw or ":" not in raw:
        return None
    status_str, _, body = raw.partition(":")
    status = int(status_str)
    if status != 200:
        return {"_http_status": status, "_body": body}
    try:
        return json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return None


class ONPEScraper(BaseScraper):
    def scrape(self) -> list[dict]:
        return asyncio.run(self._scrape_async())

    async def _scrape_async(self) -> list[dict]:
        browser = await uc.start(
            browser_executable_path=self.config.get(
                "chrome_path", "/usr/bin/google-chrome-stable"
            ),
            headless=self.config.get("headless", True),
            sandbox=False,
            browser_args=[
                "--headless=new",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/137.0.0.0 Safari/537.36",
            ],
        )
        try:
            page = await browser.get(CONVOCATORIAS_URL)
            await asyncio.sleep(self.config.get("cf_wait", CF_WAIT_SECONDS))

            title = await page.evaluate("document.title", return_by_value=True)
            if not _passed_cloudflare(str(title)):
                print(
                    f"Cloudflare no superado (titulo={title}). "
                    f"Sube el tiempo de espera en config.cf_wait."
                )
                return []

            vigentes = await self._fetch_all_pages(
                page, TIPO_LOCACION_SERVICIO, ver_concluidas=False
            )
            vigentes_concurso = await self._fetch_all_pages(
                page, TIPO_CONCURSO_PUBLICO, ver_concluidas=False
            )
            concluidas = await self._fetch_all_pages(
                page, TIPO_LOCACION_SERVICIO, ver_concluidas=True
            )
            concluidas_concurso = await self._fetch_all_pages(
                page, TIPO_CONCURSO_PUBLICO, ver_concluidas=True
            )

            all_rows = (
                vigentes + vigentes_concurso + concluidas + concluidas_concurso
            )
            return self._normalize(all_rows)
        finally:
            browser.stop()
            await asyncio.sleep(1)

    async def _fetch_one_page(
        self,
        page: uc.Tab,
        tipo_convocatoria: int,
        ver_concluidas: bool,
        page_index: int,
        page_size: int,
    ) -> dict[str, Any] | None:
        payload = _build_filter(
            tipo_convocatoria, ver_concluidas, page_index, page_size
        )
        js = _build_post_body(payload)
        raw = await page.evaluate(js, await_promise=True, return_by_value=True)
        return _parse_api_response(str(raw))

    async def _fetch_all_pages(
        self,
        page: uc.Tab,
        tipo_convocatoria: int,
        ver_concluidas: bool,
    ) -> list[dict[str, Any]]:
        label = (
            f"{'Concluidas' if ver_concluidas else 'Vigentes'} "
            f"{'ConcursoPublico' if tipo_convocatoria == 2 else 'LocacionServicio'}"
        )
        all_rows: list[dict[str, Any]] = []
        page_index = 0

        while True:
            result = await self._fetch_one_page(
                page, tipo_convocatoria, ver_concluidas, page_index, PAGE_SIZE
            )
            if result is None or result.get("_http_status"):
                print(f"  {label} pagina {page_index}: sin respuesta valida")
                break

            data = result.get("data", {})
            page_data = data.get("convocatoriasPage", {})
            rows = page_data.get("rows", [])
            total_records = page_data.get("totalRecords", 0)

            if not rows:
                break

            all_rows.extend(rows)
            total_pages = page_data.get("totalPages", 0)
            print(
                f"  {label} pagina {page_index}: "
                f"{len(rows)} registros (total {total_records}, paginas {total_pages})"
            )

            if page_index >= total_pages - 1:
                break
            page_index += 1

        return all_rows

    def _normalize(self, raw_rows: list[dict[str, Any]]) -> list[dict]:
        seen_ids: set[int] = set()
        normalized: list[dict] = []

        for row in raw_rows:
            id_perfil = row.get("idPerfil")
            if id_perfil is not None and id_perfil in seen_ids:
                continue
            if id_perfil is not None:
                seen_ids.add(id_perfil)

            rubros = [
                r.get("descripcion", "") for r in (row.get("lsRubros") or [])
            ]
            normalized.append(
                {
                    "id": id_perfil,
                    "titulo": row.get("locacionServicio") or "",
                    "denominacion": row.get("denominacion") or "",
                    "categoria": row.get("categoria"),
                    "rubros": rubros,
                    "remuneracion_soles": row.get("montoSoles"),
                    "cantidad_requerida": row.get("cantidadRequerida"),
                    "fecha_publicacion": row.get("fechaPublicacion", ""),
                    "id_proceso_electoral": row.get("idProcesoElectoral"),
                    "tipo_perfil": row.get("tipoPerfilNombre"),
                    "estado_perfil": row.get("estadoPerfil"),
                    "estado_postulacion": row.get("estadoPostulacion"),
                    "postulacion_habilitada": row.get("postulacionHabilitada"),
                    "url_lista": CONVOCATORIAS_URL,
                    "url_postulacion": f"{BASE_URL}/login",
                    "url_detalle": (
                        f"{CONVOCATORIAS_URL}"
                        f"?perfil={id_perfil}"
                        f"&proceso={row.get('idProcesoElectoral')}"
                    ),
                    "scraped_at": datetime.now().isoformat(),
                }
            )

        normalized.sort(
            key=lambda x: x.get("fecha_publicacion") or "",
            reverse=True,
        )
        return normalized


def _passed_cloudflare(title: str) -> bool:
    return CF_TITULO_BLOCKED.lower() not in title.lower()
