# v0.25 — Bélgica 1993-94 activa

La liga belga de 1993-94 se activa únicamente después de cerrar el gate de plantilla histórica. El runtime usa el ID histórico `930052`; el ID `52` de la MDB suministrada sigue bloqueado porque pertenece a otra edición temporal.

## Gate de plantilla

- 18 clubes históricos.
- 413 filas de participación recuperadas de las plantillas BDFutbol 1993-94.
- 406 identidades reales distintas.
- 7 futbolistas aparecen en dos clubes durante la misma temporada y se conservan como una sola identidad con dos etapas: Chidi Nwanu, Gunther Schepens, Thierry Pister, Flórián Urbán, Jean-Marie Abeels, Ballenghien y Luc Ernès.
- 54 identidades se reutilizan de forma segura desde el universo existente.
- 352 identidades históricas nuevas se materializan en la base.
- 61 membresías de clubes belgas pertenecientes a la edición moderna de la MDB se apartan de la plantilla activa, sin borrar sus registros.
- Plantilla activa mínima: 19 jugadores. Ningún club queda por debajo del gate de 18.

Plantillas de apertura: Anderlecht 23, Club Brugge 21, FC Seraing 19, Charleroi 20, Royal Antwerp 24, Standard Liège 23, Oostende 19, KV Mechelen 23, Beveren 23, Germinal Ekeren 23, Lommel 22, Cercle Brugge 24, RFC Liège 24, Lierse 20, Gent 24, Molenbeek 24, Waregem 27 y Genk 23.

## Identidad, posición y atributos

La reutilización de jugadores existentes exige coincidencia segura de identidad y edad histórica; los homónimos dudosos no se reaprovechan. Los jugadores nuevos reciben atributos fijos materializados a partir de comparables del propio universo 1993-94 de posición y nivel semejantes. No hay fórmulas de valoración universales en runtime.

Todos los jugadores activos de la liga tienen uno de los 18 roles especializados del juego. La procedencia de la posición queda guardada por jugador: posición histórica ya existente, curación histórica específica, identificación fiable de portero por datos de participación o inferencia documentada a partir del orden de plantilla/estructura del equipo. Las inferencias no se presentan como hechos verificados y quedan trazadas para futuras mejoras de ficha individual.

## Fotos

La identidad BDFutbol se guarda cuando ha podido verificarse sin ambigüedad. La cola fotográfica conserva el ID de jugador y el ID BDFutbol para que el descargador no dependa de coincidencias por apellido. Las imágenes incorporadas al juego se normalizan a JPEG RGB de 40x55, el formato nativo del paquete histórico. En este checkpoint quedan ya incorporadas y normalizadas las fotos verificadas disponibles durante la pasada; el resto de identidades BDFutbol confirmadas permanecen en la cola trazable para descarga, sin sustituirse por imágenes inventadas.

## Activación

`bel_tur_rus_1993_94_league_foundations.json` marca Bélgica como `active_historical_roster_gate_passed`. El source-rule histórico `930052` está además certificado como `simulation_ready`: el runtime construye 18 participantes, 34 jornadas y 306 partidos y los disputa completos. El ID moderno `52` continúa bloqueado.

Turquía y Rusia permanecen bloqueadas hasta superar el mismo gate: plantilla histórica completa, mínimo 18 reales por club, reconciliación de internacionales, posiciones y atributos revisados, control de duplicados y assets.

El detalle completo y auditable está en `data/football9394/belgium_1993_94_roster_gate_audit.json`.
