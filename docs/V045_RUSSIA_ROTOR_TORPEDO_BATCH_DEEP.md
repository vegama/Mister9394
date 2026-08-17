# v0.45 — Rusia: lote Rotor → Torpedo

Este checkpoint cambia el ritmo de profundización de Rusia: en lugar de producir una entrega por club, cierra en una sola pasada seis plantillas consecutivas del staging 1993: **Rotor Volgograd, Dynamo Moskva, Tekstilshchik Kamyshin, Lokomotiv Moskva, Spartak Vladikavkaz y Torpedo Moskva**.

## Resultado

- 159/159 filas de staging tienen ahora un perfil individual BDFutbol enlazado por ID y URL.
- Esas 159 filas corresponden a 158 identidades reales después de resolver un duplicado demostrado.
- 24 perfiles tienen además fecha de nacimiento y contexto histórico de nacimiento transcritos en esta pasada; el resto queda marcado explícitamente como metadato parcial, no rellenado por inferencia.
- Los perfiles generados enlazados quedan en la cola de retratos como `ready_for_download` salvo los que ya estaban empaquetados.
- Las posiciones exactas ya presentes en el staging se conservan. Un perfil individual de posición amplia no degrada una posición histórica más precisa ya respaldada por el staging.

## Duplicado real resuelto

`Andrey Alekseyevich Chernyshov` estaba materializado dos veces: `9497352` en Spartak Moskva y `9496652` en Dynamo Moskva. Ambos registros enlazan al mismo perfil individual BDFutol `701521`, por lo que v0.45 retira `9496652`, conserva `9497352` como identidad canónica y añade Dynamo Moskva como segundo `historical_club_spell_1993_94`.

Esto no es una fusión por transliteración o parecido de nombre. La regla queda endurecida: **un nombre parecido jamás basta; un ID de perfil individual estable, junto al contexto de club/temporada compatible, sí puede resolver una identidad duplicada**.

El caso contrario también queda protegido: los dos `Morozov` de Tekstilshchik Kamyshin siguen siendo personas diferentes porque resuelven a perfiles BDFutbol distintos (`591050` y `591054`).

## URSS / 1993

La separación histórica permanece intacta:

- `historical_birth_state` representa el Estado soberano al nacer (URSS para nacimientos soviéticos anteriores a la disolución).
- `birth_territory_country_id` sólo sirve como territorio sucesor/moderno de referencia.
- `birth_country_id` no se rellena retroactivamente con Rusia, Ucrania, Georgia, Kazajistán, Bielorrusia, Tayikistán, etc.
- `citizenship_country_ids_1993` no se deduce del lugar de nacimiento, del club, del apellido, de una nacionalidad posterior ni de la selección.
- Las transliteraciones quedan como alias de una identidad ya demostrada, nunca como criterio único para fusionar jugadores.

## Integridad

La huella rusa antes de la pasada era `e07f35db04e5979433ed1bfc3a9e2704758a636abe8f116903eb12d7c9473111`. Tras el lote cambia de forma intencionada. Todos los clubes rusos fuera del lote y de Spartak Moskva (afectado únicamente por la consolidación de Chernyshov) conservan exactamente su huella previa.

El número de objetos-jugador rusos pasa de 492 a 491 exclusivamente porque se ha retirado ese duplicado probado; no se ha perdido ninguna fila de plantilla: el staging conserva las 159 filas de los seis clubes y la fila de Dynamo apunta a la identidad canónica.

## Siguiente frente

El siguiente bloque empieza directamente en **Uralmash**, seguido por **CSKA Moskva → KAMAZ → Zhemchuzhina Sochi → Dynamo Stavropol → Lokomotiv Nizhny Novgorod → Krylia Sovetov → Luch Vladivostok → Okean Nakhodka → Rostselmash → Asmaral Moskva**.
