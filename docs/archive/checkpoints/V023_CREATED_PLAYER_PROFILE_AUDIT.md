# v0.23.0 · Auditoría profunda de perfiles creados

Esta pasada corrige la capa de atributos de los jugadores creados en 0.21/0.22 sin introducir ninguna regla global nueva de valoración.

## Decisión de producto

Los 10.528 jugadores históricos importados del snapshot siguen siendo la escala canónica. Ningún jugador original es recalculado por esta pasada. Los jugadores creados se revisan como datos fijos y auditables, utilizando perfiles de jugadores originales comparables para evitar plantillas genéricas por posición.


## Resultado

- 367 jugadores creados revisados 367/367.
- 97 medias corregidas mediante decisiones nominales explícitas; el resto se conserva tras revisión.
- 224 vectores de atributos distintos antes de la pasada; 367/367 distintos después.
- 90 grupos de clones exactos antes; 0 después.
- 0 perfiles pendientes.
- 10.528 jugadores originales: 0 cambios de hash.
- Cada alta conserva dos comparables originales, contexto, confianza y motivo de cualquier cambio.

## Cruce contra el MDB completo

También se compararon las 367 altas con los 37.312 registros de `basedatos(1).mdb`, no sólo con el snapshot jugable. Se localizaron 9 coincidencias fuertes y 2 ambiguas fuera del snapshot histórico. Los registros coincidentes pertenecen a ediciones fuente 2016/2017, por lo que se usan únicamente como evidencia de identidad/perfil y nunca como magnitud de atributos para 1993-94.

## Gate de futuras altas

Los importadores pueden generar un registro provisional para completar un lote, pero éste queda marcado como `provisional_pending_profile_review` y `profile_review_required=true`. Un checkpoint final no puede conservar jugadores en ese estado. La revisión de perfil debe materializar valores fijos y dejar trazabilidad antes de considerarlos terminados.

## Fotos BDFutbol

El registro estable y la cola BDFutbol siguen conteniendo exactamente las 367 altas reales. Se ha añadido `overall`, estado de revisión y confianza al registro maestro sin cambiar los nombres de fichero (`<source_id>.jpg`) ni incluir identidades reutilizadas.
