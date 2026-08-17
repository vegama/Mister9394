# Fuentes y trazabilidad

## Base histórica 1993-94

Fuente de trabajo recibida: `1993.zip`, con la base `1993/basedatos/basedatos.mdb` y recursos gráficos asociados.

El runtime distribuye `data/football9394/historical_snapshot.json`, una normalización trazable mediante los `source_id` originales. La MDB completa no se incluye duplicada en el repo limpio.

Verificación del corte usado por el juego:

- 23 ligas históricas en el snapshot;
- 5 torneos;
- 441 clubes;
- 10.528 futbolistas.

La presencia en el universo no implica que el club sea seleccionable al iniciar carrera. Se conservan clubes necesarios para competiciones continentales, mercado, historia o continuidad aunque no pertenezcan a una liga controlable.

## Gráficos

Del paquete fuente sólo se copian al runtime los recursos que corresponden a entidades realmente presentes en el universo 93-94: retratos disponibles, escudos y estadios. Los retratos originales son pequeños (40×55) y se muestran a tamaño compacto para no degradarlos mediante ampliaciones artificiales.

Los resultados, fichajes, lesiones, contratos inferidos y demás sucesos posteriores al comienzo de la partida son datos generados por la simulación y no se presentan como hechos históricos.
## Mundial de 1994 · convocatorias internacionales

La capa internacional USA 94 usa el **Fjelstul World Cup Database**, de Joshua C. Fjelstul, para identidad de futbolista, equipo del torneo, posición amplia y dorsal. El proyecto fuente se distribuye bajo **CC BY-SA 4.0**:

- https://github.com/jfjelstul/worldcup
- licencia declarada por el dataset: CC BY-SA 4.0.

La relación de convocatorias, seleccionadores y club del futbolista en el corte del torneo se contrasta con la relación pública de plantillas de la Copa Mundial de 1994 (clubes/edades/caps referidos al 16 de junio de 1994):

- https://en.wikipedia.org/wiki/1994_FIFA_World_Cup_squads

El runtime conserva 528 plazas históricas (24 selecciones × 22 jugadores) vinculadas a 528 identidades únicas. Los jugadores que ya existen en la fuente 1993-94 conservan sus atributos originales. Para identidades que no pueden reconciliarse con seguridad se crea un registro internacional explícitamente marcado con `attribute_source=derived_1993_94_model`; esos atributos finos son **estimaciones de gameplay**, no estadísticas históricas atribuidas a las fuentes.

Antes de usar `Otros-País`, cada candidato se reconcilia contra toda la BD existente y, si realmente es una alta, se cruza con el club declarado para el torneo. Tras la deduplicación 0.22, USA 94 se resuelve como **261 identidades existentes + 267 altas reales**. De esas altas, 2 se asignan directamente a un club jugable verificado y 265 usan contenedor; las otras asignaciones que parecían altas en 0.21 eran en realidad futbolistas ya presentes en sus clubes y ahora se reutilizan. Cuando el club real 1993-94 no pertenece a una competición jugable del universo, el jugador queda contratado por `Otros-País`. Estos contenedores no compiten ni fichan, pero pueden vender y no conceden ninguna excepción reglamentaria: el comprador sigue sujeto a las reglas históricas de extranjeros de su competición.

## Pools de selecciones · 1993

Para ampliar selecciones más allá de USA 94 se usa la relación anual de futbolistas que disputaron partidos con su selección absoluta en 1993 de National-Football-Teams. La versión 0.22 incorpora un pool explícito de 22 jugadores por país para Chile, Finlandia, Australia, Ghana y Argelia, además del pequeño lote de cierre para Yugoslavia, Paraguay, Irlanda del Norte, Hungría y Eslovaquia.

- https://www.national-football-teams.com/country/41/1993/Chile.html
- https://www.national-football-teams.com/country/66/1993/Finland.html
- https://www.national-football-teams.com/country/12/1993/Australia.html
- https://www.national-football-teams.com/country/72/1993/Ghana.html
- https://www.national-football-teams.com/country/3/1993/Algeria.html

Nombre, fecha de nacimiento, posición amplia y club indicado para ese año se tratan como datos históricos; los atributos detallados que falten siguen marcados como estimaciones derivadas de gameplay. Cada candidato se compara primero contra los 10.528 jugadores originales; las coincidencias existentes se reutilizan y las ambiguas detienen la importación.


## Profundidad Bélgica, Turquía y Rusia · 1992–94

La pasada 0.24 amplía el fondo de selección con registros históricos de National-Football-Teams en la ventana 1992–94, priorizando 1993 y usando 1994 sólo para completar futbolistas ya pertenecientes al entorno inmediato de la temporada:

- https://www.national-football-teams.com/country/20/1993/Belgium.html
- https://www.national-football-teams.com/country/192/1993/Turkey.html
- https://www.national-football-teams.com/country/152/1994/Russia.html

Las 61 altas de esta tanda se contrastan primero contra el snapshot completo y después contra los 37.312 jugadores del MDB suministrado. Sus atributos no proceden de una fórmula universal nueva ni de las magnitudes modernas del MDB: son datos de gameplay fijos revisados contra comparables originales 1993-94 y, en jugadores de perfil reconocible, con ajustes explícitos de estilo.

## Fundaciones de liga Bélgica / Turquía / Rusia 1993-94

BDFutbol se utiliza como fuente de plantilla/uso histórico para la reconstrucción progresiva de los 52 clubes de primera división de estas tres competiciones. Las URLs exactas de cada plantilla están registradas en `data/football9394/bel_tur_rus_1993_94_league_foundations.json`. La página de Anderlecht 1993-94, por ejemplo, expone la plantilla y los minutos/partidos/goles de la temporada.

Las filas de liga 52 (Bélgica), 57 (Turquía) y 15 (Rusia) del MDB **no** se consideran fuente de plantillas 1993-94: su `EdicionTemporada` es 2017. Permanecen desacopladas del registro histórico para impedir que una plantilla moderna se active con reglas antiguas. Las ligas históricas sólo se activarán cuando todos sus clubes dispongan de un mínimo de 18 futbolistas reales de 1993-94.
