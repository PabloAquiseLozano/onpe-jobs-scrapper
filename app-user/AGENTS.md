## Development

When starting the dev server, use background mode:

```
astro dev --background
```

Manage the background server with `astro dev stop`, `astro dev status`, and `astro dev logs`.

## Documentation

Full documentation: https://docs.astro.build

Consult these guides before working on related tasks:

- [Adding pages, dynamic routes, or middleware](https://docs.astro.build/en/guides/routing/)
- [Working with Astro components](https://docs.astro.build/en/basics/astro-components/)
- [Using React, Vue, Svelte, or other framework components](https://docs.astro.build/en/guides/framework-components/)
- [Adding or managing content](https://docs.astro.build/en/guides/content-collections/)
- [Adding styles or using Tailwind](https://docs.astro.build/en/guides/styling/)
- [Supporting multiple languages](https://docs.astro.build/en/guides/internationalization/)

## Producto

- **Alcance**: solo lectura pública. No hay login ni CRUD — la política RLS de Supabase ya bloquea insert/update/delete para el rol `anon`, solo `service_role` (el scraper) escribe. No agregar UI de crear/editar/borrar.
- **Fuente de verdad del estado "vigente"**: nunca confíes en el campo crudo `estado_perfil`/`estado_postulacion` que llega de la API de ONPE — el scraper (`schedule-task/scraper/onpe_scraper.py`) ya lo normaliza según en qué bucket (`verConcluidas=false` vs `true`) apareció la fila, porque ONPE casi nunca actualiza esos campos por sí solos. En el frontend, la única fuente de verdad es `esVigente()` en `src/lib/types.ts` — nunca leas `estado_perfil` directamente en un componente.
- **Detalle de convocatoria**: cada convocatoria tiene su propia página en `/convocatorias/[id].astro` (ruta dinámica SSR, sin `getStaticPaths`). Las cards del listado son un solo `<a>` que cubre toda la tarjeta (stretched-link) hacia esa ruta — no botones sueltos de "ver más".
- **Datos enriquecidos por convocatoria** (`proceso_electoral_nombre`, `modalidad`, `odpes`): el endpoint de lista de ONPE (`convocatoria/lista`) no los trae — hace falta una llamada aparte por convocatoria a `convocatoria/por-id` (ver `schedule-task/scraper/onpe_scraper.py::_fetch_detalles`). El scraper solo la hace para las convocatorias que están vigentes hoy (no para las ~200 concluidas, sería mucho tráfico extra sin necesidad). `odpes` llega de ONPE como array de texto ya formateado (`"HUAYTARA (Cantidad requerida: 16) Plazo para postulación: del ... al ..."`), no como objetos — se parsea con `parseOdpe()` en `src/lib/types.ts`, con fallback al texto crudo si el formato cambia.
- **Paginación**: el listado en `Home.astro` renderiza todas las convocatorias en el HTML (necesario para que la búsqueda/filtro sea instantánea sin round-trip a Supabase), y pagina ese resultado ya filtrado en el cliente con un selector "Mostrar 5 / 10 / 20 por página" (`#page-size`) y un índice de navegación numerado con `‹ 1 2 … N ›` (`#page-numbers`, con ventana alrededor de la página actual + primera/última). Cambiar el término de búsqueda, el filtro de estado o el tamaño de página siempre resetea a la página 1. Seguir este mismo patrón client-side para cualquier otra lista larga en vez de paginar contra Supabase (evita romper la búsqueda instantánea).

## Diseño

- Tipografía: Space Grotesk (`font-display`, títulos/cifras) + Inter (`font-sans`, cuerpo) — configurado en `@theme` dentro de `src/styles/global.css`. No usar fuentes serif/editoriales tipo Fraunces.
- Paleta: `zinc` (neutro) + `teal` (acento primario) + `emerald` (vigente) — evitar `slate`/`indigo`, ya se probaron y se pidió cambiarlos.
- Modo claro/oscuro: se controla con el atributo `data-theme` en `<html>` (no con la media query `prefers-color-scheme` sola). El toggle vive en `src/components/ui/ThemeToggle.astro`. Cualquier color nuevo debe llevar su variante `dark:`.
- **Nunca escribas un reset de CSS fuera de un `@layer`** (ej. `* { margin: 0; padding: 0 }` suelto en `global.css`). Tailwind v4 pone `utilities` en un `@layer`, y cualquier CSS sin layer explícito gana automáticamente sobre TODO lo que está en un layer — esto ya rompió todos los paddings/márgenes del sitio una vez. Si hace falta un reset, va dentro de `@layer base { ... }`.
- `import '../styles/global.css'` vive en `BaseLayout.astro`, no en cada página. Cualquier página nueva que use `BaseLayout` ya hereda los estilos automáticamente — no lo vuelvas a importar por página (una vez se nos olvidó en una ruta nueva y quedó sin estilos).
