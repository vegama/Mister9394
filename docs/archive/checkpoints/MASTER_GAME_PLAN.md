# Míster 93/94 — Plan maestro de estudio

## Nueva etapa de profundidad funcional · NF0–NF12 (abierta en 0.47)

Se abre una nueva etapa inspirada en la filosofía de gestión de Football Manager: staff real, delegación, conocimiento imperfecto, planificación, entrenamiento, táctica conductual, relaciones y consecuencias conectadas. Para evitar colisión con el antiguo bloque F1–F8 ya cerrado, el nuevo plan se identifica como **NF0–NF12**. NF0 (arquitectura humana del club y responsabilidades) está activo. Documento rector: `docs/FM_REFERENCE_FUNCTIONAL_PLAN.md`.

## Estado del plan · checkpoint 0.20.0-p10-plan-closed

**P1–P10 cerrados.** La vertical de carrera ambiciosa está completa: firma individual de partido, mercado planificado y competitivo, reglamento 1993-94 blindado, carrera internacional paralela y gate final de perfiles/nómada/invariantes longitudinales. El reparto permanece congelado y el reglamento 1993-94 es permanente: no Bosman, no liberalización futura de extranjeros y no reformas automáticas de ventanas/inscripción.

**M0–M15 siguen implementados como base funcional. R1–R10 quedan cerrados como revisión completa de producto.**

### Regla longitudinal vigente · reparto eterno (0.15)

La edad congelada es el modo predeterminado: el reparto de 1993-94 no envejece ni se retira por edad y no existe reposición mediante cantera/newgens. Los atributos sí cambian por rendimiento, entrenador, lesiones, forma, minutos, experiencia y tutela. El modo cronológico continúa como alternativa explícita y conserva los antiguos gates de retirada/cantera. Esta regla prevalece sobre las secciones históricas de F6 que describen la política anterior.

P4 queda cerrado en 0.15 con capitán/liderazgo, competencia, tutela, reacción colectiva, lesión/retorno, reencuentros y promesas de rol basadas en uso real. P5 queda cerrado en 0.17 con preparación por contexto competitivo, adaptación entre partidos y memoria entrenador-rival. P6–P10 quedan cerrados en 0.20 con firma individual, mercado ecosistémico, candado reglamentario, selección gestionable e invariantes de carrera final. Véanse `V015_FROZEN_CAST_DRESSING_ROOM.md`, `V017_P5_CLOSED_PESETA_CALIBRATION.md` y `V020_P6_P10_PLAN_CLOSED.md`.


### F1–F8 · profundización de fútbol (cerrado)

**F1 identidad ✓ → F2 entrenadores/táctica ✓ → F3 partido causal ✓ → F4 jerarquía y salud ✓ → F5 mercado orgánico ✓ → F6 carrera larga ✓ → F7 UX de profundidad ✓ → F8 gate ✓.**

La fuente recuperada en 0.8.0 se consume ahora en gameplay: 18 roles por jugador, rasgos ocultos, consistencia y atributos finos; entrenadores con táctica, calidad, rotación, cantera, relación, estrategia y desarrollo; árbitros; estadios; lesiones específicas; `OrigenVasco`; y pools nacionales de nombres para cantera.

El cierre automático F8 usa 120 partidos de Primera y obtiene 2,575 goles/partido frente al objetivo histórico 2,603, con variedad táctica, 21 arquetipos y cadenas causales de ocasión. Existe además un gate focal de diez años para edad/retirada/cantera y se revalidan los rollovers 1994-95 y 1995-96.

El longitudinal mundial completo de M15 excedió la ventana de ejecución durante esta recertificación sin assertion fallida; por tanto no se marca como re-certificado para 0.9 aunque exista un PASS de la pasada anterior. Véase `docs/F1_F8_FOOTBALL_DEPTH_CLOSED.md`.


### C1 · carrera del mánager y movilidad (cerrado en 0.11.0)

La destitución deja de terminar la partida. El mánager tiene reputación y etapas persistentes, el club que lo despide contrata un sustituto IA y se abren proyectos de la misma liga que heredan **sin recomputar** la clasificación/calendario existente. Se ha validado una trayectoria con dos destituciones y dos cambios de club consecutivos. La movilidad entre ligas durante una temporada queda deliberadamente pendiente de su propio gate de swap de competición. Véase `docs/V011_MANAGER_CAREER_MOBILITY.md`.

### L1–L5 · carrera viva y memoria (cerrado en 0.10.0)

**L1 rivalidades/memoria ✓ → L2 relación mánager–jugador ✓ → L3 historias emergentes ✓ → L4 mercado de entrenadores IA ✓ → L5 récords/archivo de etapa ✓.**

La carrera ya no olvida el significado de lo ocurrido al pulsar Continuar. Rivalidades de la MDB ganan temperatura por partidos y traspasos; la confianza jugador–mánager acumula decisiones y altera el coste real de retener al futbolista sin modificar su valoración base; los clubes IA pueden destituir y contratar entrenadores de la fuente, cambiando inmediatamente el perfil que alimenta su táctica; y las historias abiertas sólo nacen de condiciones persistidas (racha, lucha deportiva, tensión, negociación, rivalidad o banquillo) y después quedan archivadas cuando se resuelven. Récords de la etapa y balance del mánager sobreviven a los cambios de temporada. Véase `docs/V010_LIVING_CAREER.md`.

### D1–D9 · producto football-first y gate visual (cerrado)

**D1 dirección artística ✓ → D2 ficha jugador ✓ → D3 club ✓ → D4 Inicio ✓ → D5 jerarquía de información ✓ → D6 profundidad visible ✓ → D7 jornada ✓ → D8 mundo con rostro ✓ → D9 Chromium 1080p ✓.**

D9 ha renderizado las diez superficies del bucle principal en Chromium 1920×1080. No hay overflow horizontal ni texto visible por debajo de 11 px; `Guardar táctica`, cambios y ajuste táctico quedan accesibles en el primer viewport. La previa utiliza el espacio para revisar el XI en vez de mostrar un relato vacío y el postpartido elimina controles muertos. Evidencia: `docs/D9_CHROMIUM_VISUAL_GATE.md`. La build Vite de producción continúa como certificación técnica separada porque el binario no está disponible en este entorno.

## Visión

Míster 93/94 debe ser un manager de fútbol histórico completo, ágil y muy rejugable. La profundidad no vendrá de obligar al jugador a confirmar decenas de tareas, sino de que unas pocas decisiones tengan consecuencias visibles durante semanas, temporadas y carreras enteras.

Bucle objetivo: **Continuar → aparece algo relevante → decidir → preparar partido → jugar → ver consecuencias → continuar.**

Principios de producción:

- pensar mucho sobre fútbol y hacer pocos clics;
- cada pantalla debe ayudar a decidir o comprender;
- ningún botón será decorativo;
- el mundo puede contener más clubes de los que son seleccionables al crear carrera;
- la simulación de fondo debe ser barata, determinista y coherente con la simulación detallada;
- el dato histórico se distingue siempre del dato generado por la partida;
- la carrera debe poder encadenar temporadas desde 1993-94 sin perder historia;
- 1080p es la superficie principal y Continuar debe permanecer siempre accesible.

## M0 — Rendimiento como restricción de arquitectura

Separar partido detallado y simulación de fondo, cachear calendarios y fuerza de equipos, evitar reconstrucciones globales innecesarias, actualizar clasificaciones de forma incremental cuando compense y mantener guardados compactos. Objetivo: un día corriente debe sentirse instantáneo.

**Gate:** avance diario normal por debajo de 250 ms en el entorno de referencia, manteniendo determinismo y continuidad.

## M1 — Nueva carrera

Elegir liga y club con contexto útil: escudo, estadio, plantilla, nivel del núcleo, mejores jugadores, socios, presupuesto, deuda y expectativas. Inicio rápido, varios slots y autosave seguro.

**Gate:** cualquier liga regular selectable y cualquier club elegible pueden iniciar una carrera válida.

## M2 — Inicio / Bandeja del mánager

Inicio responde a dos preguntas: qué está pasando y qué tengo que decidir. Próximo partido, posición, forma, moral, bajas, contratos, objetivo, confianza y asuntos pendientes. Sólo las incidencias relevantes interrumpen el flujo.

## M3 — Plantilla, once y convocatoria

Once y banquillo reales y persistentes, disponibilidad, lesiones, sanciones, forma, moral, rendimiento, contrato y selección automática útil. El motor consume exactamente el XI guardado por el usuario.

## M4 — Táctica pequeña pero profunda

Formación, mentalidad, ritmo, presión, pase, línea defensiva, anchura, marcaje y fuera de juego. Si una orden no cambia de forma observable el comportamiento, no merece existir.

## M5 — Partido realmente jugable

Primero un directo de texto excelente: previa, reloj, narración, estadísticas, cambios, lesión, tarjetas, condición, ajustes, descanso y postpartido. Pausa, x1, x2, x4, sólo ocasiones y resultado instantáneo. No abrir 2D hasta que diez partidos seguidos en texto sigan apeteciendo.

## M6 — Futbolistas con identidad

Ficha clara con atributos, rendimiento, temporada, contrato, salud e historial de la partida. El usuario debe recordar jugadores por cómo rinden, no sólo por una media.

La referencia de densidad es la ficha clásica de PC Fútbol 7: **retrato histórico pequeño arriba a la derecha, información compacta y legible y protagonismo para datos y decisiones**. Es una inspiración de jerarquía, no una copia visual. Las fotos fuente de 40×55 se muestran pequeñas y conservando proporción; nunca como imágenes hero ampliadas y borrosas.

## M7 — Mercado que genere historias

Búsqueda, seguimiento, transferibles, libres, ofertas, contraofertas, salario, duración, competencia, negociaciones que duren días, ventas, cesiones cuando proceda y renovaciones. La IA ficha por necesidad de plantilla y coste de oportunidad.

## M8 — Economía comprensible

Caja, presupuesto, deuda, masa salarial, ingresos y consecuencias. Profundidad económica sin convertir el juego en contabilidad. Los contratos inferidos para hacer jugable la simulación se etiquetan como tales.

## M9 — Consejo, objetivos y riesgo

Expectativas según fuerza y contexto del club. Confianza basada en resultados, trayectoria, objetivos y economía, con causas comprensibles y sin despidos arbitrarios.

## M10 — Noticias nacidas del mundo

Fichajes, lesiones, goleadas, títulos, descensos, clasificaciones, récords y convocatorias generan noticias y memoria. Nada de titulares de relleno que no provengan de un hecho de la partida.

## M11 — Competiciones navegables

Clasificación, resultados, calendario, cuadros, participantes, reglas y palmarés según formato. Toda competición presente en el universo debe sentirse parte del mundo aunque no sea seleccionable como empleo inicial.

## M12 — Cierre de temporada memorable

Campeones, ascensos, descensos, Europa, estadísticas, economía y contratos desembocan en el verano, mercado y nueva temporada. El historial permanece consultable.

## M13 — IA de clubes

Evaluar plantilla, titulares, posiciones débiles, dinero, contratos, rendimiento y alternativas. Validar cada verano tamaño, cobertura, salarios, gasto, ventas, renovaciones y agentes libres.

## M14 — Pulido UX radical

Acción principal evidente, entidades pinchables, contexto conservado, sin recargas, pocos modales, filtros persistentes, atajos y operaciones habituales en uno o dos clics.

## M15 — Balance y playtests

Gates funcional, multitemporada, mundo 10 años, IA y diversión. Probar favorito, club medio, candidato al descenso y club de división inferior. Puntuar diversión, tensión, ritmo, claridad, identidad, mundo y ganas de continuar.

## Orden aprobado

Base completada: **M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8 → M9 → M10 → M11 → M12 → M13 → M14 → M15.**

Revisión de producto cerrada: **R1 sistema visual/arquitectura ✓ → R2 navegación y shell ✓ → R3 Inicio ✓ → R4 Plantilla/ficha ✓ → R5 Táctica/partido ✓ → R6 Mercado ✓ → R7 resto de superficies ✓ → R8 Nueva carrera ✓ → R9 UX profundo ✓ → R10 gates ✓.**

R1–R10 comparten una sola gramática moderna. Competiciones, economía, noticias, selecciones, club, historia y calendario están extraídos del componente raíz; Nueva carrera es un explorador de ligas/clubes y Back/Forward/F5 forman parte del contrato de navegación. El único gate no certificado en este entorno es la build/renderización Vite/Chromium por materialización incompleta de dependencias.

## Criterio de “completamente jugable”

Debe poder iniciarse con cualquier club elegible y jugar al menos tres temporadas completas sin intervención técnica, con once/convocatoria, táctica, partido interactivo, lesiones/sanciones, competiciones, mercado, contratos, economía, consejo, IA, noticias, palmarés, ascensos/descensos, Europa y transición de temporada.

El criterio emocional de salida es sencillo: **al terminar 1993-94, el jugador quiere empezar inmediatamente 1994-95.**
