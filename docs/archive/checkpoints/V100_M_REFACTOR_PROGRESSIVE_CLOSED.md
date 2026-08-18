# V1.0-M — Refactor progresivo · CERRADO

Fecha: 18-08-2026  
Base: `1.0.0-l`  
Checkpoint: `1.0.0-m-refactor-progressive-closed`

## Regla de la pasada

M no reescribe el juego ni cambia reglas de carrera. Cada extracción conserva el contrato observable y se apoya en tests de caracterización previos/existentes más snapshots nuevos de rutas y firmas.

## Backend de carrera

`manager_career.py` pasa de **361.060 B** a aproximadamente **262.803 B** (reducción ~27%). Se extraen dos bloques cohesionados sin alterar sus cuerpos de algoritmo:

- `career_history_runtime.py`: clasificación de ligas de fondo, honores, ascensos/descensos, calificadores, premios, recap y rollover de temporada;
- `career_market_runtime.py`: búsqueda/negociación, watchlist, traspasos/cesiones, listados/ofertas, decisiones de vestuario relacionadas, snapshot de mercado/economía y renovaciones.

`ManagerCareerRuntime9394` conserva exactamente las firmas previas mediante mixins. El snapshot de caracterización fija **35 firmas** movidas.

## API

`webapp.py` pasa de **51.071 B** a ~**15.088 B** y deja de ser dueño de toda la carrera. El contrato de FastAPI se divide en:

- `career_routes.py`;
- `management_routes.py`;
- `match_market_routes.py`;
- `world_routes.py`;
- `manager_route_support.py` para carga/persistencia compatible;
- `webapp_contracts.py` para payloads Pydantic.

El snapshot de caracterización conserva exactamente **88 rutas `/api/football9394/*`** (método, path y handler). Se preservan además los seams históricos `webapp.CAREER_SAVE_ROOT`, `_career_store` y `_load_manager_career` para tests/integradores existentes.

## Frontend

`Football9394App.vue` baja de **71.543 B** a ~**66.904 B** y empieza a actuar como orquestador en lugar de acumular infraestructura transversal.

Extraído:

- `useNavigationContext`: URL, F5, Atrás/Adelante y recuperación de superficie segura durante previa/directo;
- `useAsyncActionLock`: exclusión de acciones asíncronas de partido;
- `useCareerState`: ID de carrera y persistencia/restauración de contexto diario y de mercado.

El comportamiento destructivo de navegación sigue cubierto por el gate UI y los 28 SFC continúan válidos.

## CSS

`football9394-manager.css` queda como entrypoint de compatibilidad y la hoja se divide, preservando orden de cascada, en:

1. `football9394-tokens.css`;
2. `football9394-shell.css`;
3. `football9394-workspaces.css`;
4. `football9394-depth.css`;
5. `football9394-product.css`;
6. `football9394-dark.css`.

El gate UI se adapta para inspeccionar todas las capas, no para relajar reglas.

## Caracterización y regresión

- gate específico M: **5/5 PASS**;
- K + L + G: **15/15 PASS**;
- historia/mercado/economía tras extracción: **26/26 PASS**;
- subset API de persistencia/mercado/carrera/staff: **10/10 PASS**;
- frontend: estructura SFC PASS, UI quality PASS, sintaxis Vue **28/28 PASS**;
- contrato API: **88/88 rutas idénticas** respecto a L;
- contrato runtime: **35/35 firmas movidas idénticas**.

La suite completa monolítica de `test_football9394_webapp.py` vuelve a superar la ventana larga tras 15 casos sin fallo; los casos afectados se certifican por lotes, evitando declarar verde un timeout.

## Rendimiento

Medición local post-refactor (`docs/qa/V100_M_PERFORMANCE_GATE.json`):

- crear carrera: mediana **0,3439 s**;
- snapshot: **0,0443 s**;
- mercado: **0,0043 s**;
- clasificación: **0,0002 s**;
- avanzar día normal: **0,1302 s**.

La referencia longitudinal G permanece en ~3,4–4,3 s por temporada madura y ~2 s de rollover tardío, muy por debajo del guardarraíl de 12 s. No se introduce camino algorítmico nuevo en M.

## Assets

`docs/v100_m_asset_microbatch_attempt.json`: 10.195 retratos disponibles; 4 intentos nuevos, 0 descargas y 4 fallos de resolución DNS. `checkpoint_blocked=false`.

## Siguiente frente

**V1.0-N — Beta / RC**: smoke rápido, integración, destructivo, soak y playtest humano; cero P0 y P1 explícitos/finitos antes del candidato reproducible.
