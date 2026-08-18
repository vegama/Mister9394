# Estado canónico — Míster 93/94

Fecha: 18-08-2026  
Versión: **1.1.2**  
Checkpoint: **1.1.2-rc-browser-contracts-source**

## Base preservada

La línea A→M continúa cerrada. Esta pasada no cambia reglas deportivas ni reabre economía, transición longitudinal, partido, mercado, staff, entrenamiento, emoción/hitos o refactor: los utiliza como base funcional y eleva cómo los vive el jugador.

## v1.1.2 — Pasada seria de producto UX/UI · RC BROWSER CONTRACTS

Se ha ejecutado la auditoría profesional adjunta y se han aplicado cambios de alto impacto antes de entrar en RC:

- arquitectura mental del lateral: **HOY / EQUIPO / CLUB / TEMPORADA / CARRERA Y MUNDO**;
- búsqueda rápida global **Ctrl/Cmd+K** mediante `ManagerCommandPalette`;
- continuidad de decisiones Inicio → destino mediante `DecisionFocusBar`;
- design primitives comunes: `UiPageHeader`, `UiActionDock`, `UiProcessTrail`, `UiEmptyState`, `UiDataTable`;
- Plantilla conserva filtro/posición/disponibilidad/orden durante la sesión;
- Táctica, Mercado y Entrenamiento normalizan proceso y siguiente paso;
- Staff mejora microcopy de destino y estados;
- Calendario, Competiciones, Noticias y Carrera distinguen estados vacíos normales de ausencia/error;
- nuevo gate `npm run check:ux`, integrado en `npm run build`;
- auditoría integral A–L en `docs/V110_UX_AUDIT_AND_SERIOUS_PRODUCT_PASS.md`;
- plan vivo RC en `docs/PLAN_V110_SERIOUS_UX_RELEASE.md`;
- auditoría fuente preservada en `docs/reference/AUDITORIA_UX_SERIOUS_RELEASE_SOURCE.txt`.


### Continuación UX-4 / UX-5 / UX-6

- navegación de entidades con `history.state` y pestaña de ficha de jugador persistente en URL (`entityTab`);
- botón de retorno visible en `ManagerTopbar` cuando existe contexto previo;
- Noticias enlaza jugador, club y competición cuando la entidad existe;
- feedback global de operación lenta a partir de 500 ms;
- timeout de API a 15 s y errores técnicos traducidos a lenguaje de jugador;
- mutaciones idénticas concurrentes colapsadas para impedir dobles envíos accidentales;
- error de entidad persistente con **Reintentar** y **Volver**, separado del empty state;
- onboarding contextual `FirstRunGuide` para la primera carrera, retirado tras el primer partido dirigido;
- command palette con flechas/selección/Enter para jugador experto, focus trap y devolución del foco;
- enlace accesible **Saltar al contenido** y `main` focalizable como landmark de trabajo;
- Entrenamiento vuelve a mostrar de forma explícita **SIGUIENTE PASO** y **CONSECUENCIA**, protegido por el gate K.

### Benchmark BasketManager

Se han adaptado patrones de producto, no su apariencia ni sus reglas: foco de decisión, trails de proceso, action docks, empty states explicativos, tablas de trabajo, persistencia y gates UX.

### Gates ejecutados

- frontend SFC: PASS;
- UI quality histórico + v1.0 destructivo: PASS;
- nuevo UX product contract (navegación + entidades + feedback runtime + onboarding + accesibilidad teclado + workspaces): PASS;
- sintaxis Vue: **38/38**;
- release H: **7/7**;
- M refactor: **5/5** (incluye root `Football9394App.vue` <70 KB y nuevo seam `useEntityNavigation`);
- core loop + management continuity: **5/5**;
- I funcional: **4/4**; el sentinel histórico de versión `1.0.0-i` se mantiene fuera del conteo porque ya no representa la versión canónica;
- J cierre de partido: **4/4** por ejecución segmentada;
- K gestión/mercado/staff: **6/6**;
- L emoción/hitos: **6/6**;
- navegación de club + incertidumbre de scouting: **2/2**;
- destructive matchday: los 7 casos han sido validados de forma segmentada; el archivo completo monolítico excede la ventana y no se contabiliza como una ejecución completa;
- assets: 10.195 retratos preservados; microintento de 4, 0 añadidos y 4 fallos DNS, no bloqueantes.

## Evidencia visual

Las capturas `docs/visual-qa/d9-1920x1080/` se han usado como evidencia histórica, pero son anteriores al dark pass actual y a v1.1.2. No se consideran certificación del render vigente.

## Siguiente frente

**v1.1.x Beta / RC final.** La matriz responsive/zoom, la serialización de rutas y la red/doble envío ya tienen gates ejecutables. Falta el E2E sobre `frontend/dist`: F5 literal, recorrido de primera carrera, flujo experto y playtest humano sobre la build servida. Cero P0; P1 explícitos y finitos.

### Limitación de entorno actual

`npm run build` alcanza todos los gates previos y queda bloqueado únicamente en `vite build` porque el `node_modules` materializado no contiene el binario `vite`; `npm ci` no puede repararlo al no disponer de DNS/salida al registro. No se declara bundle ni Chromium actual como certificados. `test_football9394_webapp.py` sigue sin certificarse como suite monolítica porque algunas ejecuciones retienen/degradan el proceso pese a mostrar casos verdes. `test_football9394_manager_career.py`, en cambio, queda **14/14 certificado mediante ejecuciones segmentadas aisladas**, incluidos ambos rollovers; el agregado no se usa como autoridad.

## Addendum v1.1.2 — contratos browser/RC ejecutables

- Chromium source-CSS: **8/8** en 1920×1080, 1366×768, 1280×720, 1024×768 y equivalentes de 200 % de zoom.
- Bug real corregido: a ≤700 px la navegación ya no aparece arriba ni envuelve dos filas; es una barra inferior fija, horizontal y con espacio reservado en el workspace.
- `Saltar al contenido` usa patrón visualmente oculto compatible con tabulación real; command palette conserva foco/retorno.
- `navigationRoute.js` extrae serialización/parsing de ruta; gate Chromium de History API: **9/9** (sección, entidad, pestaña, Atrás, Adelante y remount desde URL/history).
- `requestTransport.js` extrae red; `npm run check:network`: **10/10** para doble POST, GET independiente, estado lento, limpieza, offline, timeout y sanitización 500.
- `test_football9394_manager_career.py`: **14/14** verificados por ejecuciones segmentadas, incluidos rollover 93/94→94/95 y repetición hasta 95/96.
- Viajes API de partido/mercado: directo hasta descanso+cambio, Resultado desde previa, negociación multidía persistente y volver previa→XI comprobados de forma aislada; los tres últimos cierran limpiamente 1/1 en la pasada final.
- `rc_production_browser_gate.py` queda listo para bundle real: nueva carrera, matriz de viewport, Ctrl+K, Inicio/Plantilla/Mercado, Atrás/Adelante y `reload()` literal. En este entorno devuelve **BLOCKED** porque no existe `frontend/dist/index.html`; no se interpreta como PASS.
- `run_rc_quality_gate.py` deja trazabilidad por gate y aislamiento de procesos para evitar que una suite monolítica contaminada o retenida convierta un timeout en un falso verde.
- Micro-lote assets v1.1.2: 4 intentos, 0 añadidos por DNS, 10.195 retratos preservados; no bloqueante.

### Bloqueo RC restante

Obtener dependencias npm completas, generar `frontend/dist`, ejecutar `python backend/tools/rc_production_browser_gate.py` y realizar playtest humano nuevo/intermedio/experto/destructivo sobre esa misma build.
