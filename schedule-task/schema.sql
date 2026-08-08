-- Esquema para ONPE Convocatorias Scraper
-- Ejecutar en el SQL Editor de Supabase

CREATE TABLE IF NOT EXISTS convocatorias (
    id SERIAL PRIMARY KEY,
    id_perfil INTEGER,
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
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (id_perfil)
);

-- Índice para búsquedas por fecha
CREATE INDEX IF NOT EXISTS idx_convocatorias_fecha_publicacion
    ON convocatorias (fecha_publicacion);

-- Índice para búsquedas por estado
CREATE INDEX IF NOT EXISTS idx_convocatorias_estado_perfil
    ON convocatorias (estado_perfil);

-- Índice para búsquedas por remuneración
CREATE INDEX IF NOT EXISTS idx_convocatorias_remuneracion
    ON convocatorias (remuneracion_soles);

-- Índice de texto para búsquedas por título
CREATE INDEX IF NOT EXISTS idx_convocatorias_titulo
    ON convocatorias USING gin (to_tsvector('spanish', coalesce(titulo, '')));

-- Habilitar Row Level Security
ALTER TABLE convocatorias ENABLE ROW LEVEL SECURITY;

-- Política: lectura pública (anon y authenticated pueden leer)
CREATE POLICY "Lectura publica de convocatorias"
    ON convocatorias FOR SELECT
    TO anon, authenticated
    USING (true);

-- Política: solo service_role puede insertar/actualizar (scraper)
-- El service_role bypassa RLS por defecto, pero lo dejamos explícito:
CREATE POLICY "Insercion solo service_role"
    ON convocatorias FOR INSERT
    TO service_role
    WITH CHECK (true);

CREATE POLICY "Actualizacion solo service_role"
    ON convocatorias FOR UPDATE
    TO service_role
    USING (true);
