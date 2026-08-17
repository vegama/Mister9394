# R7–R10 · Cierre del rediseño de producto

Checkpoint: **0.7.0-r10**

Esta pasada cierra el plan de revisión visual iniciado en R1. La decisión de producto se mantiene: Míster 93/94 es un manager contemporáneo ambientado en 1993-94. La época vive en reglas, datos, fotografías, escudos, estadios, calendarios y economía; no en cromado retro ni en tipografía diminuta.

## R7 — Resto de superficies

Se extraen del componente raíz y se unifican con la gramática moderna:

- `CompetitionsWorkspace.vue`
- `EconomyWorkspace.vue`
- `NewsWorkspace.vue`
- `NationalWorkspace.vue`
- `ClubWorkspace.vue`
- `HistoryWorkspace.vue`
- `CalendarWorkspace.vue`

Competiciones usa cabecera editorial, pestañas segmentadas, tabla/resultados/calendario/palmarés y participantes en un contexto único. Economía separa liquidez, margen de fichajes, salarios, deuda y flujo mensual. Noticias se comporta como hemeroteca. Club convierte estadio, escudo, jerarquía y consejo en una superficie de identidad. Historia funciona como archivo de carrera y Calendario como agenda deportiva.

El `Football9394App.vue` deja de contener vistas inline: el template raíz sólo orquesta workspaces.

## R8 — Nueva carrera

`CareerSetup.vue` deja de ser un formulario con dos desplegables.

El flujo es ahora:

**buscar competición → elegir competición → buscar club → comparar punto de partida → empezar**.

La ficha previa muestra escudo, estadio, tamaño de plantilla, nivel del XI, socios, presupuesto, deuda, formato y referentes. Las fotos históricas siguen mostrándose en pequeño.

## R9 — UX transversal

- La sección activa se refleja en el hash de URL.
- Back, Forward y F5 recuperan la superficie activa.
- `Continuar` queda bloqueado mientras el mundo está avanzando para evitar dobles acciones.
- Atajos de teclado amplían la navegación (`I`, `P`, `T`, `M`, `G`, `A`, `N`, `E`, `S`, `H`; `C` o espacio para continuar).
- Estados `focus-visible` son comunes a la shell y a Nueva carrera.
- Los workspaces conservan su contexto local en lugar de recargar la aplicación.

## R10 — Gates

`check:ui` ahora exige:

- suelo tipográfico de 11 px;
- ausencia de paleta/biseles retro;
- presencia de todos los workspaces R1–R8;
- ausencia de vistas inline en el componente raíz;
- explorador de Nueva carrera;
- contrato Back/Forward/F5;
- bloqueo de `Continuar` en avance.

Se añade `tools/vue-script-syntax.mjs` al `build` para comprobar la sintaxis JavaScript de todos los SFC sin depender de Vite. La compilación de templates sigue siendo responsabilidad de la build de Vite.

## Validación de este checkpoint

- `npm run check:sfc`: **PASS**.
- `npm run check:ui`: **PASS**.
- JavaScript extraído de los 23 SFC Vue comprobado con `node --check`: **23/23 PASS**.
- `test_football9394_webapp.py` + `test_football9394_manager_career.py`: **25/25 PASS**.
- `test_football9394_m4_m8_gameplay.py`: **9/9 PASS**.
- `test_football9394_m9_m15_gameplay.py`: **12/12 PASS**.
- Regresión dirigida total de cierre: **46/46 PASS**.
- Backend/motor no modificado en R7–R10; permanecen vigentes los gates longitudinales certificados en el checkpoint de origen.
- Build de Vite: **no certificada en este entorno**. `npm ci` vuelve a bloquearse durante la materialización de dependencias y no llega a crear el binario de Vite. No se registra un falso PASS.

## Estado del plan

**R1 ✓ · R2 ✓ · R3 ✓ · R4 ✓ · R5 ✓ · R6 ✓ · R7 ✓ · R8 ✓ · R9 ✓ · R10 ✓**

La revisión de producto queda cerrada en código y gates estáticos/manager. El único gate que requiere un entorno frontend con dependencias completas es la build/renderización real de Vite/Chromium.
