# v0.24.0 · profundidad internacional y fundación Bélgica/Turquía/Rusia 1993-94

Esta pasada continúa la ampliación de selecciones con un objetivo distinto al antiguo gate mínimo de 22: disponer de aproximadamente 40 futbolistas reales por país para que lesiones, sanciones, forma y decisiones del seleccionador no dejen una selección sin alternativas.

## Valoración: misma escala del juego, ninguna norma nueva

Las altas externas se comparan con jugadores originales 1993-94 de la misma posición y nivel. El resultado se materializa como atributos fijos; los futbolistas importantes reciben además un perfil específico cuando un comparable no expresa bien su estilo. Ningún jugador original es recalculado por esta pasada.

La auditoría acumulada queda en 428 jugadores externos revisados, 428 vectores de atributos distintos, cero perfiles pendientes y cero modificaciones de hash en los 10.528 jugadores fuente.

## Profundidad de selección

La tanda `bel_tur_rus_national_depth_0.24` contiene 61 altas reales:

- Bélgica: +15; pool internacional explícito = 41.
- Turquía: +40; pool internacional explícito = 49, con un núcleo histórico 1992-94 de 40 documentados.
- Rusia: +6; pool internacional explícito = 42.

Las tres selecciones pasan mínimos de porteros, defensas, medios y delanteros. Cada alta guarda posición histórica, club histórico, fuente de identidad y lote de creación.

## Doble reconciliación de identidad

Antes de crear, el candidato se busca contra el snapshot. La tanda nueva se volvió a cruzar contra los 37.312 jugadores del MDB completo. Resultado: 61/61 sin coincidencia oculta exacta y sin colisión nominal que justifique fusionar. La auditoría global de las 428 altas sigue a cero en colisiones fuertes/ambiguas y duplicados exactos generados.

## Registro para fotos

`created_players_registry.{json,csv}` y `bdfutbol_photo_queue.{json,csv}` incluyen ahora `historical_club_1994` y `historical_position_1993_94`. Sólo las altas verdaderas entran en la cola; una identidad reutilizada conserva su ID original y se documenta en reconciliación.

## Bélgica, Turquía y Rusia: fundación de las ligas

`bel_tur_rus_1993_94_league_foundations.json` registra los 52 participantes históricos (18 + 16 + 18), clasificación de referencia, URL exacta de plantilla BDFutbol y gate mínimo de 18 jugadores reales por club.

No se han activado todavía esas ligas. Los source IDs 52/57/15 del MDB pertenecen a `EdicionTemporada=2017` y además tienen tamaños modernos (16/18/16), por lo que están bloqueados como bindings runtime 1993-94. La reconstrucción histórica usará IDs propios (930052/930057/930015) cuando todos los clubes superen el gate de plantilla. Esto evita mezclar rosters modernos con reglas de 1993-94.

## Gates

- `test_football9394_v024_bel_tur_rus_depth.py`: 8/8.
- Los tests de datos antiguos ya no congelan cifras como 367 altas o 29 `Otros-*`; comprueban invariantes y coherencia de informes, permitiendo ampliar la BD sin convertir el crecimiento válido en una regresión.
- El resto de la recertificación dirigida y los gates frontend se ejecutan antes de empaquetar el checkpoint.
