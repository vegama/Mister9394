# v1.1.0 — Serious UX source gate

Fecha: 18-08-2026

## Resultado

**SOURCE PASS / RUNTIME RC PENDIENTE.**

### Frontend source

- `python backend/tools/sync_product_version.py --check` → PASS `1.1.0`.
- `npm run check:version` → PASS.
- `npm run check:sfc` → PASS.
- `npm run check:ui` → PASS, conserva R1–R10 + D1–D9 + continuidad destructiva v1.0.
- `npm run check:ux` → PASS, nuevo contrato de arquitectura mental, foco de decisión, primitivas y workspaces core.
- `npm run check:vue` → PASS, 35/35 SFC.

### Backend focal

- `test_football9394_v100_m_refactor.py` → 5/5.
- `test_football9394_v100_core_loop.py` + `test_football9394_v100_management_continuity.py` → 5/5.
- `test_football9394_v100_destructive_matchday.py`: el archivo completo excede la ventana después de cinco casos; se valida por caso y los 7/7 escenarios quedan verdes de forma segmentada:
  - roja irreversible;
  - descanso estable y reanudación;
  - límite histórico de dos cambios;
  - lesión de entrenamiento repara XI guardado;
  - tarjetas de liga → sanción/noticia/disponibilidad;
  - postpartido → tabla/moral/noticia/siguiente partido;
  - lesión en vivo → médico/noticia/siguiente XI.

### Build / browser

`npm run build` ejecuta y supera todos los gates previos, pero no puede invocar Vite en este entorno porque `node_modules/.bin/vite` no está disponible. No se declara build PASS ni se genera visual QA nuevo.

### Visual

Las capturas D9 1920×1080 del repo se revisan como evidencia histórica, no como render vigente: preceden al dark pass y a esta v1.1.0. El RC debe regenerarlas con Chromium.

### Assets paralelo

`python backend/tools/run_asset_pass.py --limit 4 --report docs/v110_ux_asset_microbatch_attempt.json`:

- fotos runtime antes/después: 10.195 / 10.195;
- 4 intentos;
- 0 descargas;
- 4 fallos temporales de resolución DNS;
- `checkpoint_blocked=false`.

## Criterio de salida

Esta evidencia cierra la **pasada source UX v1.1.0**, no el RC. El siguiente gate obligatorio es runtime/browser/playtest.
