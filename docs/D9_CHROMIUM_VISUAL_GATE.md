# D9 · Gate visual Chromium 1920×1080

Checkpoint: `0.9.3-d9-chromium-visual-gate`

## Qué se valida

D9 deja de ser un gate teórico. Se han renderizado en **Chromium real a 1920×1080** las diez superficies que forman el bucle principal: Inicio, Plantilla, ficha de jugador, ficha de club, Táctica, Mercado, Competiciones, previa, directo y postpartido.

El harness utiliza los **templates Vue exactos del repo**, `core.css` y `football9394-manager.css`, con una muestra deliberadamente exigente basada en FC Barcelona 1993-94: Romário, Stoichkov, Laudrup, Guardiola, Koeman, Camp Nou, Johan Cruyff y un Clásico como partido de referencia. Los gráficos históricos del propio repo se hidratan en la captura.

No es una sustitución de `vite build`: el bundle de producción sigue sin poder ejecutarse en este entorno porque el binario Vite no está materializado. D9 certifica composición y legibilidad en navegador; el gate técnico de empaquetado Vite permanece separado.

## Problemas encontrados por el navegador y corregidos

1. **Táctica** tenía un `small` anidado que Chromium resolvía a 9,16 px aunque el CSS estático parecía respetar el suelo de 11 px. Se fija explícitamente a 11 px.
2. La lista «Quién ejecuta el plan» empujaba `Guardar táctica` por debajo de 1080p. La lista tiene ahora scroll interno y el guardado queda visible.
3. La **previa** reservaba una gran caja blanca a un relato que todavía no existía. Ese espacio se convierte en un último control del XI: titulares, posición, condición y banquillo.
4. En **directo**, estadísticas + selección de cambios + `Hacer cambio` + `Ajustar táctica` quedaban parcialmente por debajo del pliegue. Se compactan marcador, contexto y rail lateral sin reducir legibilidad.
5. En **postpartido** seguían apareciendo controles de sustitución ya inútiles. Desaparecen al finalizar para priorizar la lectura causal y las estadísticas.

## Resultado del gate

- 10/10 superficies renderizadas sin error de página ni warning Vue del componente.
- 10/10 sin overflow horizontal.
- 0 elementos visibles por debajo de 11 px.
- Táctica: acción `Guardar táctica` visible en el primer viewport.
- Previa/directo: todas las acciones de banquillo y táctica visibles a 1080p.
- Postpartido: sin controles muertos; lectura + causas + datos visibles.
- Mercado y Competiciones: flujo principal completo dentro del viewport.
- Inicio, Plantilla, jugador y club conservan scroll vertical **intencional** para profundidad; la primera pantalla contiene las decisiones y contexto futbolístico prioritarios.

La evidencia visual está en `docs/visual-qa/d9-1920x1080/` y el resumen de métricas en `metrics.json`.

## Limitación explícita

`npm run build` ejecuta correctamente `check:sfc`, `check:ui` y `check:vue`, pero termina en `vite: not found`. Por tanto:

- **D9 composición/legibilidad Chromium: CERRADO.**
- **Build Vite de producción en este entorno: NO CERTIFICADA.**
