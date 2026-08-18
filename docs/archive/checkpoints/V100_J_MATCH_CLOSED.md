# V1.0-J — Partido · cierre canónico

Fecha: 18-08-2026  
Checkpoint: `1.0.0-j-match-closed`

## Contrato cerrado

La jornada del usuario es una sola transacción de producto: previa reversible hasta el inicio, partido dirigido o Resultado sobre el mismo motor, commit único y postpartido persistente. En liga, ese commit resuelve también el resto de encuentros de la jornada y expone sus marcadores desde el propio postpartido y desde Inicio.

El informe final guarda `round_summary` como derivación de los resultados canónicos ya persistidos; no existe un segundo generador de marcadores para la UI. También guarda `postmatch_context` con clasificación del club, moral, confianza del consejo, próximo encuentro y bajas conocidas para la siguiente convocatoria.

## Estados destructivos protegidos

Se mantienen los gates de roja/segunda amarilla, lesión forzada sin cambios, límite histórico de dos sustituciones, táctica al descanso, sanción consumida en la jornada siguiente, aplazado, rival pendiente, calendario vacío y coherencia lesión/sanción entre ficha, briefing, Inicio, calendario y noticias.

## UX

El postpartido muestra la jornada completa de la competición con el partido del usuario destacado. Al cerrar el partido, Inicio conserva el resumen de la última jornada y permite saltar a Competiciones. Las consecuencias importantes quedan juntas antes de volver al ritmo normal de Continuar.

## Gates ejecutados

- V1.0-J específico: 4/4 PASS.
- V1.0 core loop: 3/3 PASS.
- destructivo wave4: 6/6 PASS.
- destructivo base: 6 casos PASS antes del límite de ejecución + séptimo caso aislado 1/1 PASS.
- frontend: SFC structure PASS; UI quality PASS; Vue syntax 28/28 PASS.
- assets: 10.195 fotos conservadas; 4 intentos nuevos fallidos por DNS, trazados y no bloqueantes.

Siguiente frente canónico: **V1.0-K — Mercado, staff y entrenamiento**.
