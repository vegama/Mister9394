# Estado canónico — Míster 93/94

Fecha: 18-08-2026  
Versión: **1.1.2**  
Checkpoint: **1.1.2-rc-production-playtest-candidate**

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

## Evidencia RC de producción

El repositorio incluye `deploy_dist` y se ha ejecutado el bundle compilado real contra FastAPI real mediante Chromium. El gate de producción queda **58/58 PASS** y el playtest de personas **18/18 PASS**. Las capturas vigentes están en `docs/visual-qa/rc-production-browser/` y `docs/visual-qa/rc-persona-playtest/`.

P1/P2 encontrados durante el render real y corregidos: contraste de Nueva carrera; topbar sticky rota por `overflow-x:hidden`; superficies claras heredadas en Mercado; previa/postpartido fuera de la gramática oscura; orientación global `Inicio` dentro del partido; hueco de media fila en postpartido; estados vacíos de Inicio sin separación; resaltados excesivamente claros en tabla/consejo.

## Gates vigentes

- producción Chromium sobre bundle compilado: **58/58**;
- personas nuevo/experto/partido→consecuencia: **18/18**;
- frontend: version/SFC/UI/UX PASS, network **10/10**, Vue **38/38**;
- release H + refactor M: **13/13**;
- carrera longitudinal: **14/14 segmentada**, incluidos 93/94→94/95→95/96;
- no quedan P0/P1 conocidos en los recorridos certificados.

## Decisión actual

**RC candidate jugable.** UX-4, UX-5, UX-6 y UX-7 quedan validados sobre el bundle compilado; UX-8 tiene playtest ejecutable de persona nueva, experta y ciclo partido→consecuencia. El launcher real ya ha sido ejecutado por HTTP: health, index y assets pasan **6/6**. Sólo queda sin reproducir en este entorno la navegación Chromium directa a ese localhost por política corporativa; la misma build sí está ejercida en Chromium mediante el modo policy-safe.

### Limitación de entorno

El Chromium gestionado de este entorno aplica `URLBlocklist=["*"]` y rechaza `http://127.0.0.1` con `ERR_BLOCKED_BY_ADMINISTRATOR`. El navegador mantiene `http_static_server_certified=false` dentro del gate Chromium, pero el servidor HTTP/launcher se certifica por separado con `rc_launcher_http_smoke.py` **6/6**. El modo `policy-safe` ejecuta el mismo JS/CSS de `deploy_dist`, proxýa sus `/api` al backend real y ha permitido validar History API, Atrás/Adelante, `page.reload()` literal, red, doble clic y los recorridos de juego. No se presenta el bloqueo del navegador corporativo como fallo del producto ni como PASS del servidor HTTP.

La evidencia detallada está en `docs/qa/V112_RC_PRODUCTION_PLAYTEST.md`.
