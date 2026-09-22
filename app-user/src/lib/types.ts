export interface Convocatoria {
  id_perfil: number;
  titulo: string;
  denominacion: string | null;
  categoria: string | null;
  rubros: string[] | null;
  remuneracion_soles: number | null;
  cantidad_requerida: number | null;
  fecha_publicacion: string | null;
  id_proceso_electoral: number | null;
  proceso_electoral_nombre: string | null;
  modalidad: string | null;
  odpes: string[] | null;
  tipo_perfil: string | null;
  estado_perfil: number;
  estado_postulacion: string | null;
  url_lista: string | null;
  url_postulacion: string | null;
  url_detalle: string | null;
  scraped_at: string | null;
}

/**
 * El scraper guarda dos señales de estado separadas: `estado_perfil` (si el
 * proceso electoral sigue vigente) y `estado_postulacion` (si SIGLOC todavía
 * acepta postulaciones para ese perfil). Un perfil puede seguir "vigente" en
 * el proceso pero ya tener la postulación cerrada — eso ya no está disponible
 * aunque `estado_perfil` diga 0.
 */
export function esVigente(c: Pick<Convocatoria, 'estado_perfil' | 'estado_postulacion'>): boolean {
  return c.estado_perfil === 0 && c.estado_postulacion !== '1';
}

/** Salarios como "1.00" son valores de scraping fallidos, no ofertas reales. */
export function tieneRemuneracionValida(c: Pick<Convocatoria, 'remuneracion_soles'>): boolean {
  return c.remuneracion_soles == null || c.remuneracion_soles > 10;
}

export interface Odpe {
  distrito: string;
  cantidad: string | null;
  plazoInicio: string | null;
  plazoFin: string | null;
  raw: string;
}

const ODPE_PATTERN = /^(.+?)\s*\(Cantidad requerida:\s*(\d+)\)\s*Plazo para postulaci[oó]n:\s*del\s*(.+?)\s*al\s*(.+)$/i;

/**
 * ONPE devuelve cada ODPE ya formateada como texto ("HUAYTARA (Cantidad
 * requerida: 16) Plazo para postulación: del 19/09/2026 08:00 AM al
 * 25/09/2026 11:59 PM") en vez de campos separados. Si el formato cambia,
 * cae de vuelta al texto crudo en `raw` en vez de romper.
 */
export function parseOdpe(raw: string): Odpe {
  const match = raw.match(ODPE_PATTERN);
  if (!match) {
    return { distrito: raw, cantidad: null, plazoInicio: null, plazoFin: null, raw };
  }
  const [, distrito, cantidad, plazoInicio, plazoFin] = match;
  return { distrito, cantidad, plazoInicio, plazoFin, raw };
}
