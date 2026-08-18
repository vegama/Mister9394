# QA y release gate — Míster 93/94

## Gate de versión

```bash
python backend/tools/sync_product_version.py --check
cd frontend && npm run check:version
```

Debe existir una sola versión: `VERSION` = API = frontend = manifiesto.

## Gate backend rápido

```bash
pytest -q backend/tests/test_football9394_v100_h_release.py
pytest -q backend/tests/test_football9394_webapp.py backend/tests/test_football9394_manager_career.py backend/tests/test_football9394_world_career.py
```

## Gate frontend/build

```bash
cd frontend
npm ci
npm run build
```

`build` ejecuta antes `check:version`, `check:sfc`, `check:ui`, `check:ux` y `check:vue`.

## Gate launcher de producción

Con `frontend/dist` presente:

```bash
python run_football9394.py --no-browser
```

Comprobar:

1. `/api/football9394/health` devuelve `ok=true` y la versión canónica;
2. `/` devuelve el frontend de producción;
3. crear carrera → guardar → detener proceso → relanzar → cargar/continuar;
4. truncar intencionadamente el primario después de haber generado backup y verificar recuperación del backup;
5. confirmar que saves/backups/logs están fuera del repo.

## Pirámide de QA hacia RC

- Smoke por pasada: versión, import, API, save/load, build.
- Integración diaria: carrera, partido, mercado, economía, transición.
- Destructivo semanal: F5/Atrás/Adelante, doble envío, cierre durante guardado, saves antiguos, mercado en fecha límite, partido con bajas y cambios agotados.
- Soak candidato: 3/10/20/30 temporadas y métricas de salud.
- Playtest humano: claridad, continuidad de tareas y tiempo hasta decisión.

Un timeout del entorno no se registra como fallo funcional: los bloques largos deben ejecutarse por segmentos y conservar resultados verificables.


## Evidencia RC vigente — 18-08-2026

Bundle disponible en `deploy_dist` y ejecutado realmente en Chromium contra FastAPI mediante el modo policy-safe.

```bash
PYTHONPATH=. python backend/tools/rc_production_browser_gate.py --policy-safe
PYTHONPATH=. python backend/tools/rc_persona_playtest.py
PYTHONPATH=. python backend/tools/rc_launcher_http_smoke.py
cd frontend
npm run check:version
npm run check:sfc
npm run check:ui
npm run check:ux
npm run check:network
npm run check:vue
cd ..
PYTHONPATH=. pytest -q backend/tests/test_football9394_v100_h_release.py backend/tests/test_football9394_v100_m_refactor.py
```

Resultado vigente: producción **58/58**, personas **18/18**, launcher HTTP **6/6**, network **10/10**, Vue **38/38**, H+M **13/13**. Carrera longitudinal conserva evidencia **14/14 segmentada**.

El Chromium gestionado bloquea navegación normal a localhost (`ERR_BLOCKED_BY_ADMINISTRATOR`), de modo que no se certifica aquí el servidor HTTP estático. `--policy-safe` no sustituye el bundle: inyecta el JS/CSS compilado de `deploy_dist` y enruta las llamadas al backend real para ejercer la aplicación. El launcher y su servidor HTTP sí están certificados por transporte con `rc_launcher_http_smoke.py` (health/index/assets 6/6). Lo único no reproducible aquí es que Chromium gestionado abra directamente ese localhost.

Ver `docs/qa/V112_RC_PRODUCTION_PLAYTEST.md`.
