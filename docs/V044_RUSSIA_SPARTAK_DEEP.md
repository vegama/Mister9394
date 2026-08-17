# V0.44 — Rusia: Spartak Moskva profundo

Checkpoint: `0.44.0-russia-spartak-deep`.

## Objetivo

Rusia se abre únicamente después de comprobar que la huella completa heredada de v0.43 es exactamente `f73e73c7dee70fd00d82f9679d189677161a662bc72b71a5a723584fb5715cfa`. La primera pasada profunda se limita a Spartak Moskva; los otros 17 clubes permanecen congelados y su SHA-256 agregado coincide antes y después.

## Política histórica rusa

Desde este checkpoint se separan expresamente cinco dimensiones que antes podían confundirse:

1. **Lugar de nacimiento**: texto geográfico documentado (`historical_birth_place_text`).
2. **Estado soberano en el momento del nacimiento**: `historical_birth_state` (por ejemplo `USSR` o `German Democratic Republic`).
3. **Territorio sucesor/moderno del lugar**: `birth_territory_country_id`, sólo como contexto geográfico y de búsqueda.
4. **Ciudadanía/nacionalidad en 1993**: `citizenship_country_ids_1993`, que no se infiere de lugar de nacimiento, club, apellido, una nacionalidad posterior ni de la selección.
5. **Selección representada**: historial independiente (`represented_selection_history`) y países representados por año.

Para nacidos en territorio soviético antes de la disolución no se rellena `birth_country_id` con Rusia, Ucrania, Uzbekistán, Estonia, Lituania, etc. retroactivamente. En Spartak quedan 32 nacimientos bajo soberanía URSS y uno bajo RDA (Aleksandr Bondar, nacido en Magdeburgo en 1967).

Las transliteraciones también se separan de la identidad. Se conservan las variantes de las fuentes y nunca se fusionan dos personas por similitud ortográfica sin evidencia estable adicional. El caso más visible es `Pogodin` en la plantilla de BDFutbol frente a `Serhiy Anatoliyovych Pohodin` en el perfil individual.

## Spartak Moskva

Se profundizan los **33/33 jugadores del staging fijado**:

- 33 perfiles individuales BDFutbol enlazados.
- 33 fechas de nacimiento materializadas/revisadas.
- 33 estados históricos de nacimiento separados del territorio sucesor.
- alias/transliteraciones preservados para los 33.
- altura/peso incorporados cuando el perfil individual los ofrece.
- posiciones exactas sólo cuando la fuente las sostiene; si el perfil es amplio o está vacío, queda señalado como tal.
- ciudadanía 1993 no inventada: los 33 quedan pendientes cuando no hay evidencia específica suficiente.
- selección representada separada de ciudadanía y lugar de nacimiento.

### Casos de identidad/selección que fijan el modelo

- **Andrey Pyatnitsky**: nacido en Tashkent bajo URSS; el territorio sucesor es Uzbekistán. Su historial de selecciones atraviesa URSS/CIS, Uzbekistán y Rusia, por lo que ninguna de esas dimensiones puede usarse como sustituto automático de las demás.
- **Valeriy Kechinov**: nacido en Tashkent bajo URSS; representó Uzbekistán antes de representar posteriormente a Rusia. No se fuerza una selección rusa en 1993.
- **Ilya Tsymbalar**: nacido en Odesa bajo URSS; mantiene por separado territorio ucraniano y su secuencia internacional Ucrania → Rusia.
- **Serhiy Pohodin/Pogodin** y **Yuri Nikiforov**: lugar/territorio ucraniano e internacionalidad se conservan como datos independientes.
- **Gintaras Staučė**: nacido en Alytus bajo URSS; territorio lituano y selección lituana quedan separados del Estado al nacer.

## Conflicto resuelto

El staging heredado daba a **Ramiz Mamedov** `21/05/1972`. El perfil individual BDFutbol y una segunda fuente independiente coinciden en `21/08/1972`, que pasa a ser el dato canónico. El conflicto queda registrado en `russia_source_conflicts_v044.json` en vez de sobrescribirse silenciosamente.

## Correcciones de posición

Se eliminan seis inferencias anteriores que contradicen o exceden la evidencia individual:

- Aleksandr Bondar: delantero → defensa.
- Valeriy Kechinov: delantero centro → centrocampista.
- Dmitriy Gradilenko: delantero → defensa.
- Vladimir Baksheev: extremo izquierdo inferido → centrocampista amplio.
- Sergey Krestov: lateral izquierdo → delantero.
- Mikhail Rekuts: mediocentro defensivo inferido → defensa amplio.

En **Alexey Sergeev** el perfil individual no informa posición; se conserva provisionalmente el central del staging, pero marcado como inferencia pendiente de corroboración, no como posición exacta BDFutol.

## Deriva de fuente

La página actual de plantilla de BDFutbol muestra además `Shmykov`, `Masalitin`, `Ternavskiy` y `Alenichev`, que no estaban en el staging fijado de 33. No se añaden automáticamente en v0.44: primero debe resolverse si la diferencia procede de altas/bajas, convocatorias o del criterio temporal de la fuente. La cardinalidad rusa no cambia por deriva no reconciliada.

## Integridad y QA

- SHA-256 Rusia antes: `f73e73c7dee70fd00d82f9679d189677161a662bc72b71a5a723584fb5715cfa`.
- SHA-256 Rusia después: `e07f35db04e5979433ed1bfc3a9e2704758a636abe8f116903eb12d7c9473111`.
- El cambio es intencional y limitado a Spartak Moskva.
- SHA agregado de los otros 17 clubes antes/después: `13cfff122639c1edc512e710ba53df297c447065ec1136fac43fc5f650df738e`.
- Registro de jugadores y cola de fotos siguen sincronizados uno a uno; Cherchesov, Popov y Radchenko se enriquecen como identidades canónicas preexistentes y no se introducen en el registro de jugadores creados.
- Regresión rusa/identidad + gates heredados relevantes: **53/53 tests verdes**.

## Siguiente frente

La cola rusa queda materializada en `russia_deepening_queue_v044.json`. El siguiente club es **Rotor Volgograd**, seguido de Dynamo Moskva, Tekstilshchik Kamyshin, Lokomotiv Moskva, Spartak Vladikavkaz y el resto de la liga, aplicando desde el principio exactamente la misma separación histórica y el mismo control de integridad por club.
