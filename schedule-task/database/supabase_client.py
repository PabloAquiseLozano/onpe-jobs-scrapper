import os
from typing import Any

from supabase import create_client, Client


def get_supabase_client(use_service_role: bool = False) -> Client:
    url = os.getenv("SUPABASE_URL")
    if not url:
        raise ValueError("SUPABASE_URL no esta definida en .env")

    if use_service_role:
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    else:
        key = os.getenv("SUPABASE_KEY")

    if not key:
        role = "SUPABASE_SERVICE_ROLE_KEY" if use_service_role else "SUPABASE_KEY"
        raise ValueError(f"{role} no esta definida en .env")

    return create_client(url, key)


def upsert_convocatorias(data: list[dict[str, Any]]) -> dict[str, int]:
    sb = get_supabase_client(use_service_role=True)

    rows = [
        {
            "id_perfil": item.get("id"),
            "titulo": item.get("titulo"),
            "denominacion": item.get("denominacion"),
            "categoria": item.get("categoria"),
            "rubros": item.get("rubros", []),
            "remuneracion_soles": item.get("remuneracion_soles"),
            "cantidad_requerida": item.get("cantidad_requerida"),
            "fecha_publicacion": item.get("fecha_publicacion"),
            "id_proceso_electoral": item.get("id_proceso_electoral"),
            "proceso_electoral_nombre": item.get("proceso_electoral_nombre"),
            "modalidad": item.get("modalidad"),
            "odpes": item.get("odpes", []),
            "tipo_perfil": item.get("tipo_perfil"),
            "estado_perfil": item.get("estado_perfil"),
            "estado_postulacion": item.get("estado_postulacion"),
            "postulacion_habilitada": item.get("postulacion_habilitada"),
            "url_lista": item.get("url_lista"),
            "url_postulacion": item.get("url_postulacion"),
            "url_detalle": item.get("url_detalle"),
            "scraped_at": item.get("scraped_at"),
        }
        for item in data
    ]

    if not rows:
        return {"inserted": 0, "total": 0, "reconciled_concluded": 0}

    result = sb.table("convocatorias").upsert(
        rows, on_conflict="id_perfil"
    ).execute()

    inserted = len(result.data) if result.data else 0

    # Cualquier fila que sigue marcada vigente en la base de datos pero no
    # aparecio en el scrape de hoy como vigente (ni siquiera por venir de un
    # id_perfil que ya no trae la API en ningun bucket) ya no esta
    # disponible en realidad. Se cierra explicitamente en vez de dejarla
    # vigente para siempre.
    vigente_ids_hoy = [
        row["id_perfil"] for row in rows if row["estado_perfil"] == 0
    ]
    reconciled = 0
    if vigente_ids_hoy:
        recon = (
            sb.table("convocatorias")
            .update({"estado_perfil": 1, "estado_postulacion": 1})
            .eq("estado_perfil", 0)
            .not_.in_("id_perfil", vigente_ids_hoy)
            .execute()
        )
        reconciled = len(recon.data) if recon.data else 0

    return {"inserted": inserted, "total": len(rows), "reconciled_concluded": reconciled}


def fetch_convocatorias(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    estado: int | None = None,
    min_remuneracion: float | None = None,
    max_remuneracion: float | None = None,
) -> dict[str, Any]:
    sb = get_supabase_client()
    query = sb.table("convocatorias").select("*", count="exact")

    if search:
        query = query.ilike("titulo", f"%{search}%")
    if estado is not None:
        query = query.eq("estado_perfil", estado)
    if min_remuneracion is not None:
        query = query.gte("remuneracion_soles", min_remuneracion)
    if max_remuneracion is not None:
        query = query.lte("remuneracion_soles", max_remuneracion)

    query = query.order("fecha_publicacion", desc=True)
    query = query.range((page - 1) * page_size, page * page_size - 1)

    result = query.execute()
    return {
        "data": result.data or [],
        "count": result.count or 0,
        "page": page,
        "page_size": page_size,
        "total_pages": -(-result.count // page_size) if result.count else 0,
    }


def fetch_convocatoria_by_id(convocatoria_id: int) -> dict[str, Any] | None:
    sb = get_supabase_client()
    result = sb.table("convocatorias").select("*").eq(
        "id_perfil", convocatoria_id
    ).limit(1).execute()
    if result.data:
        return result.data[0]
    return None


def fetch_stats() -> dict[str, Any]:
    sb = get_supabase_client()
    result = sb.table("convocatorias").select("*", count="exact").execute()
    total = result.count or 0

    vigentes = sb.table("convocatorias").select(
        "*", count="exact"
    ).eq("estado_perfil", 0).execute().count or 0

    concluidas = sb.table("convocatorias").select(
        "*", count="exact"
    ).eq("estado_perfil", 1).execute().count or 0

    return {
        "total": total,
        "vigentes": vigentes,
        "concluidas": concluidas,
    }
