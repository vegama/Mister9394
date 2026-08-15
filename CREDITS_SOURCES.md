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
