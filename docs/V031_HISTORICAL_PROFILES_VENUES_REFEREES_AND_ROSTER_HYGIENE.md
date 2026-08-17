# v0.31.0 — perfiles históricos, biografías, estadios, árbitros e higiene de plantillas

## Objetivo

Esta pasada continúa la reconstrucción 1993-94 de Bélgica, Turquía, Rusia y Grecia sin convertir huecos históricos en datos inventados. El trabajo prioriza identidad, posición específica, biografía visible, retrato histórico, estadio y árbitro, conservando siempre el origen del dato.

## Higiene previa de plantillas

Antes de enriquecer perfiles se detectaron colisiones de identificadores heredados del MDB: algunos IDs de club reutilizados arrastraban jugadores ajenos a 1993-94. Se eliminaron 142 asignaciones contaminantes que no pertenecían al staging histórico verificado: 60 en Bélgica, 47 en Turquía y 35 en Rusia. No se eliminan identidades reales que aparecen en dos clubes durante la propia temporada por un traspaso.

Plantillas activas tras la limpieza:

- Bélgica: 406 jugadores / 18 clubes.
- Turquía: 414 jugadores / 16 clubes.
- Rusia: 492 jugadores / 18 clubes.
- Grecia: 496 jugadores / 18 clubes.
- Total: 1.808 jugadores activos en las cuatro ligas.

## Perfiles y posiciones

Se han curado 103 perfiles con fuente individual o plantilla detallada de temporada. 43 exigieron una corrección real de rol específico. Cuando cambia el rol, los atributos se rematerializan alrededor de la misma valoración global usando comparables históricos de la posición correcta; no se aplica ninguna fórmula 75/25.

Los casos donde la fuente sólo dice `Defender`, `Midfielder` o equivalente amplio conservan explícitamente esa incertidumbre. No se inventa lateralidad ni especialización para cerrar un contador.

## Biografías de temporada

Los 1.808 jugadores activos reconstruidos cuentan ahora con `historical_biography_1993_94`, una reseña breve en español generada únicamente a partir de datos ya respaldados por el staging/fuente: club, posición, apariciones, titularidades, minutos, goles cuando proceda y fecha de nacimiento si existe. Cada reseña conserva URL y etiqueta de fuente, además de un bloque de evidencia estructurado.

Siete identidades aparecen en más de un club en el staging por movimientos durante la temporada. La biografía conserva la lista de clubes de staging en vez de duplicar la persona.

## Retratos

Se han incorporado 16 retratos BDFutbol nuevos comprobados individualmente y normalizados al formato nativo del proyecto: JPEG RGB 40×55. El registro y la cola usan el estado canónico `bundled_normalized_bdfutbol`; no se marca como descargada una foto que no existe físicamente.

Los IDs nuevos de esta pasada son:

`9495316, 9495319, 9495337, 9495336, 9495331, 9495327, 9495348, 9495354, 9495342, 9494093, 9496352, 9496353, 9496354, 9496355, 9496357, 9496358`.

## Estadios

Grecia queda cerrada para los 18 clubes de Alpha Ethniki 1993-94 con recinto histórico enlazado. Rusia añade los 16 estadios que faltaban en los clubes reconstruidos. En Rusia se cruza la tabla de temporada con registros de partidos de 1993 para evitar nombres modernos en recintos que han cambiado de denominación.

No se importan capacidades, dimensiones o calidad de césped modernas como si fueran valores de 1993-94. Esos campos permanecen nulos hasta tener fuente temporal adecuada.

Quedan 20 clubes con estadio histórico pendiente: 6 belgas y 14 turcos.

## Árbitros

Bélgica dispone de un pool completo de 25 árbitros de la Pro League 1993-94 con apariciones y disciplina de la página histórica de temporada. Grecia codifica únicamente los 11 nombres publicados por RSSSF de un total declarado de 45; el dataset lo etiqueta expresamente como subconjunto, no como lista completa.

Rusia y Turquía siguen abiertas en árbitros. No se añaden nombres cuando la fuente encontrada no permite demostrar que pertenecen exactamente a la temporada objetivo.

La asociación/nacionalidad del árbitro no se reutiliza como país de nacimiento: `birth_country_id` permanece nulo salvo evidencia biográfica específica.

## Fuentes principales de esta pasada

- BDFutbol: fichas individuales, retratos y plantillas históricas.
- Transfermarkt: plantillas detalladas 1993-94 y listado arbitral belga 1993-94.
- RSSSF: Alpha Ethniki 1993-94 y subconjunto arbitral griego publicado.
- Wikipedia, página de temporada 1993 Russian Top League: relación club/recinto como punto de partida.
- Wildstat: registros de partidos rusos de 1993 para comprobar denominaciones de estadio de época.

Las URLs concretas se guardan también en los registros de datos/auditoría correspondientes.

## Artefactos de auditoría

- `data/football9394/historical_profiles_metadata_audit_v031.json`
- `data/football9394/historical_biographies_audit_v031.json`
- `data/football9394/historical_metadata_gaps_v031.json`
- `data/football9394/bdfutbol_photo_normalization_v031.json`
- `data/football9394/bdfutbol_photo_normalization_v031_batch2.json`
- `data/football9394/release_audit_0.31.0.json`

## Validación

La batería dirigida final cubre source catalog, runtime snapshot, reconciliación de identidades, profundidad BEL/TUR/RUS, perfiles TUR/RUS/GRE, roster completo v0.30 y todas las invariantes nuevas de v0.31. Resultado: 60 pruebas superadas. `compileall` del backend también finaliza correctamente.
