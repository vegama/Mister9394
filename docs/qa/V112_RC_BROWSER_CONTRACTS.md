# v1.1.2 — RC browser contracts · evidencia de cierre source/browser

Fecha: 18-08-2026

## Qué se certifica en este checkpoint

1. **Responsive/zoom con Chromium real sobre CSS vigente + DOM representativo**: 8/8 casos verdes en 1920×1080, 1366×768, 1280×720, 1024×768 y equivalentes de layout a 200 %.
2. **Navegación browser-source**: 9/9 en History API real de Chromium para sección, entidad, pestaña, Atrás, Adelante y reconstrucción del documento desde URL/history.
3. **Red/doble envío**: 10/10 en `npm run check:network`: mutación duplicada colapsada, GET independiente, estado lento, limpieza, offline, timeout y sanitización HTTP 500.
4. **Frontend source gates**: version, SFC, UI, UX, network y Vue 38/38 pasan antes de invocar el bundle.
5. **Release/refactor**: H 7/7 y M 5/5.
6. **Carrera longitudinal**: `test_football9394_manager_career.py` 14/14 mediante invocaciones segmentadas, incluidos 93/94→94/95 y repetición hasta 95/96.
7. **Viajes API críticos**: directo hasta descanso/cambio, Resultado desde previa, negociación multidía persistente y regreso previa→XI se verifican por casos aislados; los tres últimos cierran limpiamente en 1/1 cada uno en esta pasada final.

## Bugs RC encontrados y corregidos

### Navegación móvil colocada arriba a zoom alto

A ≤700 px el sidebar estaba en flujo DOM con `position: sticky; bottom: 0`; en Chromium, a 512×384 y 683×384 efectivos, aparecía antes de la topbar y podía envolver en dos filas.

Corrección:

- barra inferior `position: fixed`;
- una sola fila horizontal sin wrap;
- navegación desplazable en X;
- `safe-area-inset-bottom`;
- espacio inferior reservado en workspace;
- gate browser que comprueba posición inferior, altura de una fila y topbar arriba.

### Skip link no entraba de forma fiable en tabulación

El patrón basado en `transform: translateY(-160%)` se sustituyó por ocultación visual de 1 px + `clip-path`, restaurando tamaño/visibilidad al foco. El gate comprueba Tab → “Saltar al contenido” → Enter → `main`.

### Red sólo protegida por inspección estática

La lógica se extrajo a `requestTransport.js` y ahora es ejecutable sin Vue. El gate verifica que dos POST idénticos simultáneos ejecutan una única petición real del transporte.

## Gate de producción materializado

`python backend/tools/rc_production_browser_gate.py`

Cuando exista `frontend/dist`, el gate:

- levanta FastAPI + SPA desde el mismo origen;
- crea una carrera nueva si aparece el setup;
- comprueba el first-run guide;
- ejecuta matriz de viewport;
- usa Ctrl+K para llegar a Mercado;
- navega Plantilla ↔ Mercado;
- ejecuta Atrás, Adelante y `page.reload()` literal;
- registra errores de consola/page.

## Qué NO se certifica todavía

El entorno actual no contiene `frontend/dist/index.html` y `vite` no está instalado. `npm run build` pasa todos los gates previos y falla únicamente al invocar `vite build` con `vite: not found`.

Por tanto:

- la matriz 8/8 es **browser source-CSS**, no el bundle final;
- el remount de ruta no se presenta como F5 literal de producción;
- el E2E de `frontend/dist` queda **BLOCKED**, nunca PASS;
- el playtest humano sobre build final sigue pendiente.

## Deuda de suites monolíticas

Algunas suites FastAPI/carrera retienen o degradan el proceso cuando acumulan muchas sesiones en la misma invocación. Los casos autoritativos de RC se ejecutan aislados/segmentados. No se convierte una línea de puntos seguida de timeout en un pase.

## Assets paralelos

Micro-lote v1.1.2: 4 descargas intentadas, 0 añadidas por fallo DNS, 10.195 retratos preservados. No bloquea el checkpoint.

## Evidencia final del build

`npm run build` ejecuta y supera version, SFC, UI, UX, network y Vue 38/38. A continuación termina con código 127 exclusivamente al intentar `vite build` (`vite: not found`). `rc_production_browser_gate.py` devuelve código 2 / `BLOCKED` porque no existe `frontend/dist/index.html`.

## Bloqueo único para RC final

1. `npm ci` con acceso a las dependencias bloqueadas por lockfile.
2. `npm run build` hasta generar `frontend/dist`.
3. `python backend/tools/rc_production_browser_gate.py` verde.
4. Playtest humano: nuevo, intermedio, experto/teclado y destructivo.
5. Cero P0 y P1 restantes finitos/documentados.
