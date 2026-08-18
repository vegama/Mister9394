# V1.0-H — Release hygiene / cierre técnico

Fecha: 18-08-2026  
Versión canónica: `1.0.0-h`  
Checkpoint: `1.0.0-h-release-hygiene-closed`

## Alcance cerrado

- `VERSION` como única fuente de versión de producto.
- API FastAPI y `/api/football9394/health` leen la versión canónica.
- Vite inyecta la misma versión en la UI; `package.json`, lock y manifiesto se validan contra `VERSION`.
- README y documentación canónica reducidos a estado, roadmap, arquitectura y QA; 57 documentos históricos archivados sin pérdida.
- Launcher único `python run_football9394.py` para producto integrado; `--dev-api` queda sólo para desarrollo.
- Rutas de usuario por plataforma para `saves/`, `backups/` y `logs/`, con overrides `MISTER9394_*`.
- Guardado JSON atómico con temporal, `fsync`, validación antes del replace, backup conocido-válido y segundo escalón `.prev`.
- Recuperación automática primario → backup → backup anterior, preservando copia diagnóstica del primario corrupto.
- Stores de carrera de manager y mundo conectados al mismo contrato de persistencia y al backup configurable.
- FastAPI puede servir `frontend/dist` y API desde el mismo origen cuando existe el build de producción.

## QA ejecutado en este cierre

- `pytest -q backend/tests/test_football9394_v100_h_release.py` → **7/7 PASS**.
- `pytest -q backend/tests/test_football9394_webapp.py backend/tests/test_football9394_career_economy.py backend/tests/test_football9394_career_market.py` → **33/33 PASS**.
- subset de persistencia/selección/dashboard de `test_football9394_manager_career.py` → **5/5 PASS**.
- `test_football9394_v100_core_loop.py` → **3/3 PASS**.
- `python backend/tools/sync_product_version.py --check` → **PASS VERSION 1.0.0-h**.
- `npm run check:version` → PASS.
- `npm run check:sfc` → PASS.
- `npm run check:ui` → PASS.
- `npm run check:vue` → **28/28 SFC PASS**.
- Gate launcher real: arrancar → crear carrera → guardar → detener → relanzar → cargar → **PASS**. Save probado: 14.126.557 bytes, backup byte-idéntico, log persistente.
- Recuperación de primario truncado y caída a `.prev` con backup más reciente también corrupto → **PASS** mediante tests H.

## Build frontend en este sandbox

El código y todos los checks previos al build pasan. La ejecución de `npm ci` no puede certificarse dentro de este sandbox porque el runtime no resuelve `registry.npmjs.org` (`Temporary failure in name resolution` / `ENOTCACHED` al forzar modo offline) y el ZIP de entrada no traía `node_modules` ni `frontend/dist`.

Esto se registra como **BLOCKED_ENV**, no como fallo funcional ni como PASS inventado. El gate reproducible que debe ejecutarse en un entorno con acceso al registry sigue siendo:

```bash
cd frontend
npm ci
npm run build
```

Una vez generado `frontend/dist`, el launcher de producción lo sirve desde el mismo origen que la API.

## Pasada paralela de assets

Ejecutado `backend/tools/run_asset_pass.py --limit 12`. Resultado: inventario runtime estable en 10.195 fotos; 12 descargas intentadas, 0 nuevas y 12 fallos de resolución DNS. Informe: `data/football9394/asset_pass_h_release.json`. El frente principal no se bloquea por política.

## Regresiones largas

La suite backend completa y algunos archivos destructivos exceden la ventana máxima de ejecución del sandbox. Los tramos terminados no mostraron fallos; los timeouts se registran como límite del ejecutor, no como verde ni rojo. Los gates directamente afectados por H sí se ejecutaron de forma segmentada y están arriba.

## Salida

H queda implementada de principio a fin en código, estructura, persistencia, versionado, launcher y documentación. La única certificación que no puede producir este entorno es la descarga/instalación de dependencias necesaria para materializar `frontend/dist`; queda explícitamente trazada como bloqueo externo de build.
