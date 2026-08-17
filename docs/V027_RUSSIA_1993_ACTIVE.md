# v0.27 — Rusia 1993 activa

La liga rusa de 1993 queda activada mediante el identificador histórico `930015`. La fila MDB moderna `15` continúa bloqueada: no se reutiliza una edición posterior como si fuese la temporada de 1993.

El gate materializa 18 clubes con un núcleo de 18 futbolistas reales por club: 324 filas y 324 identidades históricas distintas. Se reutilizan 16 jugadores ya presentes cuando la identidad está verificada explícitamente y se crean 308 identidades nuevas. La importación excluye 35 pertenencias de época moderna que contaminaban IDs de clubes antiguos.

La reconciliación evita fusiones difusas por apellido. Casos sensibles como Dmitri Popov, Dmitri Radchenko y Stanislav Cherchesov reutilizan su identidad original y no aparecen en el registro de jugadores creados. Los roles especializados se conservan cuando existe fuente individual y las inferencias restantes quedan marcadas como tales.

Los atributos se materializan de forma fija en la escala original del juego usando comparables históricos; no existe ninguna regla 75/25 en fútbol. Cuando sólo está disponible la edad de la temporada, el runtime conserva esa edad histórica sin inventar una fecha de nacimiento.

Gate: 18 clubes, 324 identidades, mínimo 18 activos por club, `930015` operativo y `15` bloqueado.
