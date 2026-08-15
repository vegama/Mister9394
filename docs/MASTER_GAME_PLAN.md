# Míster 93/94 — Plan maestro de estudio

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

**M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8 → M9 → M10 → M11 → M12 → M13 → M14 → M15.**

## Criterio de “completamente jugable”

Debe poder iniciarse con cualquier club elegible y jugar al menos tres temporadas completas sin intervención técnica, con once/convocatoria, táctica, partido interactivo, lesiones/sanciones, competiciones, mercado, contratos, economía, consejo, IA, noticias, palmarés, ascensos/descensos, Europa y transición de temporada.

El criterio emocional de salida es sencillo: **al terminar 1993-94, el jugador quiere empezar inmediatamente 1994-95.**
