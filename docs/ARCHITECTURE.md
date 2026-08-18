# Arquitectura canónica — Míster 93/94

## Capas

- `backend/app/football9394/`: dominio, simulación, carrera persistente y API.
- `frontend/src/football9394/`: shell y superficies jugables Vue.
- `data/football9394/`: snapshot histórico normalizado, auditorías y assets runtime.
- `backend/tests/`: caracterización, reglas, integración y gates longitudinales.
- `frontend/tools/`: validaciones estructurales, UI, sintaxis Vue y versión.

## Versión

`VERSION` es la fuente única. `product_meta.py` la expone al backend; Vite la inyecta al frontend; `sync_product_version.py --check` y `frontend/tools/version-check.mjs` impiden metadatos divergentes.

## Producción

`run_football9394.py` es el launcher canónico. En producción FastAPI sirve `frontend/dist` y `/api/football9394/*` desde el mismo proceso/origen. `--dev-api` conserva un modo sólo-backend para desarrollo.

## Datos del usuario

`app_paths.py` resuelve una raíz de datos por plataforma. Por defecto se separan:

- `saves/` — estado primario de carrera;
- `backups/` — último save conocido como válido;
- `logs/` — salida persistente del launcher/API.

Todos admiten override por variables `MISTER9394_*`.

## Persistencia segura

`atomic_json_store.py` aplica el contrato común de persistencia:

1. valida el primario existente antes de convertirlo en backup;
2. escribe backup temporal y fuerza `fsync`;
3. escribe el nuevo save temporal y fuerza `fsync`;
4. relee y valida el temporal;
5. reemplaza atómicamente el primario;
6. fuerza sincronización de directorio donde el SO lo permite;
7. al cargar, si el primario falla, intenta el backup válido y conserva copia diagnóstica del corrupto.

Los stores de carrera del mánager y mundo usan este contrato.

## Refactor progresivo V1.0-M

La primera extracción pre-RC ya está materializada: `ManagerCareerRuntime9394` compone runtimes de historia/rollover y mercado; FastAPI agrupa routers por dominio; el root Vue delega navegación, persistencia de contexto y locks asíncronos; y el CSS conserva un entrypoint estable sobre seis capas ordenadas. Los snapshots de rutas y firmas en `backend/tests/fixtures/` son contratos de compatibilidad.

## Límite antes del RC

No se abre una segunda reescritura arquitectónica en N. Cualquier extracción adicional debe responder a un P0/P1 demostrado por QA y conservar los contratos de caracterización de M.
