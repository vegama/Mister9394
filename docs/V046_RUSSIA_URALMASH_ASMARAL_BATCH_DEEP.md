# v0.46 — Rusia: Uralmash → Asmaral, lote final de clubes

Este checkpoint cierra de una sola pasada los once clubes rusos que quedaban pendientes en el staging 1993-94: **Uralmash, CSKA Moskva, KAMAZ, Zhemchuzhina Sochi, Dynamo Stavropol, Lokomotiv Nizhny Novgorod, Krylia Sovetov, Luch Vladivostok, Okean Nakhodka, Rostselmash y Asmaral Moskva**.

## Resultado

- 300/300 filas del lote tienen un perfil individual BDFutbol enlazado mediante ID estable y URL.
- Los recuentos de staging son 25 + 29 + 29 + 27 + 28 + 23 + 26 + 24 + 27 + 29 + 33 = 300.
- Esas 300 apariciones corresponden a **294 identidades individuales**: seis perfiles aparecen en dos clubes del propio lote.
- Además, cinco de esas 294 identidades ya estaban materializadas y profundizadas en checkpoints anteriores. Por tanto, se retiran **11 objetos-fuente duplicados** y permanecen 289 objetos del nuevo lote, más cinco identidades canónicas anteriores que absorben su spell histórico.
- Ninguna identidad se fusiona por apellido, transliteración o parecido textual: la puerta de fusión es el **ID de perfil individual estable** y un contexto histórico de club/temporada compatible.
- Todas las apariciones de club permanecen en el staging y en `historical_club_spells_1993_94`, incluso cuando varias filas resuelven a una sola persona.

## Duplicados resueltos

Dentro del propio lote se consolidan seis perfiles repetidos: Novosadov (CSKA/KAMAZ), Fakhrutdinov (KAMAZ/Krylia), Maslov (Dynamo Stavropol/Rostselmash), Minibaev (Dynamo Stavropol/Rostselmash), Spanderashvili (Dynamo Stavropol/Rostselmash) y Zakharov (Luch/Okean).

Cinco filas adicionales apuntaban a identidades ya presentes en el universo: Sosnitsky, Matveev, Krutov, Iljin y Kovtun. Se conserva como canónico el objeto ya profundizado y se añade el nuevo paso por club a su historial, evitando degradar el trabajo anterior.

## URSS, nacionalidad y transliteración

La política histórica queda igual de estricta que en v0.45: lugar de nacimiento, Estado soberano al nacer, territorio sucesor moderno, ciudadanía/nacionalidad en 1993 y selección representada son hechos independientes. Haber nacido en la URSS o jugar en un club ruso no asigna automáticamente Rusia ni ningún otro Estado sucesor. Las transliteraciones se guardan como alias, nunca como llave de identidad.

## Integridad

La huella rusa previa era `731ae8da21ba76f6b73182adcec485f53bce47989481a81552774d358d3d39b1`. El número de objetos-jugador asociados directamente a clubes rusos pasa de 491 a 480 por las once retiradas demostradas; no desaparece ninguna aparición histórica, porque las 300 filas permanecen y todas resuelven a su identidad canónica.

Fuera de los jugadores objetivo y de las identidades canónicas que necesariamente reciben un nuevo spell, los demás objetos rusos se comparan byte a byte y permanecen sin cambios.

## Estado del frente ruso

Con este checkpoint quedan cerrados los **18/18 clubes rusos materializados** en esta liga: Spartak Moskva, los seis del lote v0.45 y estos once. `russia_deepening_queue_v046.json` queda con cola vacía y `league_club_batch_complete=true`.
