# Míster 93/94

Manager de fútbol histórico centrado en la temporada 1993-94 y en carreras persistentes multitemporada.

## Estado · checkpoint 0.24.0-bel-tur-rus-1993-data

**P1–P10 siguen cerrados; 0.24 continúa la expansión internacional con prioridad absoluta a identidad y realismo.** No se introduce una fórmula nueva de valoración: los jugadores creados se materializan como datos fijos comparándolos con futbolistas originales 1993-94 de la misma posición/nivel, con perfiles específicos para los nombres relevantes. Los 10.528 jugadores originales permanecen intactos.

La auditoría acumulada cubre ahora **428 altas históricas externas**. Todas se comparan contra los 10.528 jugadores originales y las nuevas incorporaciones de esta pasada se contrastan además contra los **37.312 registros del MDB completo**. El resultado actual mantiene cero colisiones fuertes/ambiguas y cero duplicados exactos generados. El caso de control Dmitri Popov continúa resuelto como el único ID original 515 del Racing.

La profundidad de selección se amplía específicamente en **Bélgica, Turquía y Rusia**: los pools con nacionalidad internacional explícita quedan en 41, 49 y 42 futbolistas respectivamente. La tanda 0.24 crea 61 jugadores reales (15 belgas, 40 turcos y 6 rusos), todos con club/posición histórica documentados, revisión de perfil cerrada y registro permanente para el flujo de fotos BDFutbol. El objetivo de producto ya no es sólo tener 22 convocables, sino aproximarse a 40 opciones reales por selección para absorber lesiones y sanciones.

La reconstrucción de las ligas belga, turca y rusa 1993-94 queda iniciada de forma segura en `data/football9394/bel_tur_rus_1993_94_league_foundations.json`: **52 clubes históricos** con sus páginas de plantilla BDFutbol y reglamentos de época. No se activan todavía como ligas jugables porque las filas 52/57/15 del MDB suministrado pertenecen a la edición 2017; reutilizarlas mezclaría plantillas modernas. Esos IDs están deliberadamente bloqueados y cada futura liga histórica tendrá un ID runtime propio. La activación exige un mínimo de 18 jugadores 1993-94 reales por club.

El registro de altas y la cola de fotos conservan ahora también `historical_club_1994` y `historical_position_1993_94`, además de ID, nombre, nacimiento, país, lote/fuente, control de duplicados y campos BDFutbol. Véase `docs/V024_BEL_TUR_RUS_1993_DATA.md`.

**P1–P10 permanecen cerrados.** El plan ambicioso de carrera completado en 0.20 se conserva como base: P6 firma estadística individual; P7 mercado de planificación; P8 reglamento 1993-94 congelado; P9 carrera internacional; P10 gates de carrera. Véase `docs/V020_P6_P10_PLAN_CLOSED.md`.

La economía de carrera usa ahora una escala de pesetas 1993-94 mucho más expresiva: el valor de mercado crece con fuerza en la élite (un 89 se calibra alrededor de 450 M ptas.), las fichas inferidas comparten esa escala y la IA/mercado se han reequilibrado para que clubes modestos sigan encontrando objetivos realistas. Los importes siguen siendo estimaciones de gameplay cuando la fuente no contiene un dato histórico contractual concreto.


La **edad congelada es ahora la política predeterminada** de carrera: el reparto histórico de 1993-94 no envejece cronológicamente, no se retira por edad y no es sustituido por cantera/newgens. Esto es una concesión deliberada al realismo para preservar el apego al reparto original. La profundidad longitudinal permanece: rendimiento, minutos, entrenador, lesiones, forma, adaptación, tutela y experiencia pueden mejorar o deteriorar atributos concretos. La carrera cronológica sigue disponible como alternativa explícita.

P4 quedó cerrado con una vertical profunda: capitán y líderes, competencia por puestos, tutela entre futbolistas del reparto inicial, reacción colectiva a lesiones/ventas importantes, reencuentros y **promesas explícitas de rol** evaluadas por las titularidades reales de los siguientes ocho partidos. Cumplir o romper una promesa cambia relación y satisfacción, nunca la capacidad neutral del jugador. Véase `docs/V015_FROZEN_CAST_DRESSING_ROOM.md`.

La 0.11 amplía la carrera viva: una destitución ya no termina la partida. El mánager conserva reputación, récords e historial, recibe proyectos y puede encadenar etapas en distintos clubes de la misma liga. La 0.10 mantiene además la **carrera viva con memoria**: rivalidades persistentes, relación mánager–jugador con consecuencias contractuales, historias emergentes que se abren y resuelven por hechos reales, mercado de entrenadores IA y récords/archivo de la etapa. D1–D9 y F1–F8 permanecen cerrados. Véase `docs/V010_LIVING_CAREER.md`.

El repo contiene únicamente el dominio de fútbol Míster 93/94, su frontend, tests, snapshot normalizado y los gráficos históricos utilizados por las entidades del mundo activo.

El motor mantiene **M0–M15 como base funcional**, el rediseño moderno **R1–R10 cerrado** y la profundización futbolística **F1–F8 cerrada en esta pasada**. Jugadores, entrenadores, táctica, partido, plantilla, mercado y carrera larga consumen ya la información recuperada de la MDB en lugar de reconstruirla artificialmente.


### D1–D9 · profundidad visible, bucle futbolístico y gate 1080p

La ficha de jugador y la ficha de club siguen siendo las superficies de referencia, pero el nuevo lenguaje ya se ha propagado al bucle diario. Inicio se organiza como una jornada —próximo rival, posición, forma, decisiones, figuras, tensiones y noticias—; Plantilla y Tácticas muestran encaje del XI y conflictos con el plan; Mercado explica por qué un objetivo puede encajar; y el directo incorpora previa con entrenador/plan rival, tres amenazas, árbitro y estadio, además de una lectura causal al terminar.

El entrenador fuente del club controlado sigue apareciendo sólo como **entrenador al inicio / referencia histórica**: el plan actual es el del jugador. El contrato D1–D8 queda automatizado en `frontend/tools/ui-quality.mjs`. Detalle en `docs/D1_D8_FOOTBALL_FIRST_PRODUCT.md`.

**D9 queda cerrado como gate de composición Chromium 1920×1080**: Inicio, Plantilla, jugador, club, Táctica, Mercado, Competiciones, previa, directo y postpartido se han renderizado con los templates/CSS reales y datos 93/94 representativos. La pasada corrigió tamaño tipográfico real, visibilidad de Guardar táctica, espacio muerto de previa, controles del banquillo y postpartido. `vite build` sigue siendo un gate técnico separado no certificado porque el binario Vite no está disponible en este entorno.

La revisión visual cubre shell, Inicio, Plantilla, ficha, Tácticas, directo, Mercado, Competiciones, Economía, Noticias, Selecciones, Club, Historia, Calendario y Nueva carrera. La auditoría de fuente está en `docs/MDB_DEEP_SOURCE_AUDIT.md` y el cierre F1–F8 en `docs/F1_F8_FOOTBALL_DEPTH_CLOSED.md`.

La base de juego heredada mantiene:

- consejo, objetivos, confianza explicable y riesgo de destitución con inercia;
- noticias causales y hemeroteca persistente;
- navegador universal de competiciones, reglas, resultados, calendarios y palmarés;
- cierre de temporada, archivo histórico, verano y pretemporada real;
- ritmo contextual: pulsos cortos en pretemporada y avance hacia partido/incidencia durante la temporada;
- puestos especializados y compatibilidad posicional en once, mercado e IA;
- reglas de extranjeros por competición para usuario e IA;
- 18 jugadores como suelo de plantilla, objetivos dinámicos de profundidad de 20–24 y XI legal como gate separado;
- IA que protege puestos estructurales, repara plantillas y no vende al único portero;
- jerarquía de clubes dinámica y gradual, sin convertir una gran temporada en un salto instantáneo de categoría;
- economía longitudinal recalibrada para conservar diferencias de tamaño sin crecimiento explosivo;
- gate longitudinal de 10 temporadas con controles deportivos, económicos y de plantilla, certificado en la pasada M15; en 0.9 la recertificación completa excede la ventana y se complementa con el gate F6 focal de diez años + rollovers 1994-95/1995-96.
- La certificación histórica de **174 tests de fútbol** de M15 se conserva como referencia; el cierre 0.9 añade sus propios gates dirigidos y no presenta el longitudinal completo como re-certificado.


**Profundización F1–F8 cerrada en 0.9.0-f1-f8-depth-closed**: identidad de jugador, entrenadores fuente, trece formaciones, causalidad de partido, jerarquías/tensión, lesiones específicas persistentes, mercado por necesidad/encaje, edad dinámica, retiradas, cantera/newgens fuente y gate de realismo quedan conectados al runtime. El gate de 120 partidos queda en 2,575 goles/partido frente al objetivo 2,603 de Primera 1993-94.

**Auditoría profunda de fuente cerrada en 0.8.0-source-recovery**: la MDB ya no se trata como un simple origen de jugadores/clubes. Se recuperan entrenadores, tácticas, árbitros, roles, patrones, lesiones, estadios, ciudades/regiones/clima, países, nombres ponderados e infraestructura de prensa, con niveles explícitos de confianza temporal. Entrenadores y árbitros ya afectan al runtime; la polivalencia y rasgos fuente llegan a la ficha/motor de selección; y `OrigenVasco` gobierna la política de fichajes del Athletic.

**Rediseño de producto R1–R10 cerrado en 0.7.0-r10**: shell, Inicio, Plantilla, ficha, Táctica, directo, Mercado, Competiciones, Economía, Noticias, Selecciones, Club, Historia, Calendario y Nueva carrera comparten la misma gramática moderna.

El plan completo está en `docs/MASTER_GAME_PLAN.md`. Los cierres y la revisión activa están documentados en:

- `docs/BLOCK_01_FOUNDATION_GAMEPLAY.md`
- `docs/BLOCK_02_TACTICS_MATCH_MARKET_ECONOMY.md`
- `docs/BLOCK_03_M9_M15_COMPLETE_MANAGER.md`
- `docs/R1_MODERN_PRODUCT_REDESIGN.md`
- `docs/R2_R6_MODERN_CORE_WORKSPACES.md`
- `docs/R7_R10_PRODUCT_REDESIGN_CLOSED.md`
- `docs/F1_F8_FOOTBALL_DEPTH_CLOSED.md`
- `docs/MDB_DEEP_SOURCE_AUDIT.md`
- `docs/D1_D3_REFERENCE_SURFACES.md`
- `docs/D1_D8_FOOTBALL_FIRST_PRODUCT.md`
- `docs/D9_CHROMIUM_VISUAL_GATE.md`
- `docs/V1_AMBITIOUS_CAREER_PLAN.md`
- `docs/V015_FROZEN_CAST_DRESSING_ROOM.md`
- `docs/V020_P6_P10_PLAN_CLOSED.md`
- `docs/V021_STUDIO_USA94_NATIONAL_TEAMS.md`

## Ejecutar backend

```bash
python run_football9394.py
```

## Frontend

```bash
cd frontend
npm ci
npm run dev
```

La build de producción requiere que las dependencias npm estén disponibles. El chequeo estructural SFC puede ejecutarse sin iniciar la aplicación:

```bash
npm run check:sfc
npm run check:ui
npm run check:vue
```

## Datos

El runtime consume `data/football9394/historical_snapshot.json`. La MDB fuente completa se utiliza para trazabilidad/verificación y no se duplica en el repo limpio. Los clubes fuera del selector de carrera pueden seguir existiendo en el universo cuando una competición o la historia los necesita.

Los contratos/salarios de jugador que la MDB no proporciona de forma utilizable se marcan como datos inferidos por la carrera; no se presentan como hechos históricos. La MDB sí contiene contratos/sueldos de entrenador, pero pertenecen a una fuente de edición temporalmente mixta y requieren curación antes de etiquetarlos como 1993-94.
