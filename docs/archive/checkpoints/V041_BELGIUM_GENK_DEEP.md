# v0.41.0 — Belgium: Genk deep profile pass

Bélgica sigue siendo el frente activo. Rusia no se toca en este checkpoint.

## Genk

Se profundizan los 23 futbolistas ya existentes del Genk 1993-94 y se enlazan con su perfil individual de BDFutbol. No se crean jugadores de relleno ni identidades nuevas.

Resultado de huecos belgas:

- fecha de nacimiento: **183 → 160** (-23)
- nacionalidad/identidad internacional: **169 → 148** (-21)
- país de nacimiento estructurado: **194 → 176** (-18)
- altura: **262 → 250** (-12)
- peso: **330 → 324** (-6)

La diferencia entre -23 fechas y -18 países de nacimiento es deliberada: tres nacidos en la antigua Yugoslavia (Suad Katana, Frane Bućan e Ismet Mulavdić) conservan el Estado histórico en texto y no reciben retrospectivamente el id de Bosnia-Herzegovina/Croacia como Estado de nacimiento.

## Posiciones y atributos

Se corrigen 15 roles que procedían de inferencias débiles. Cuando BDFutbol sólo documenta `Defender`, `Midfielder` o `Forward`, el jugador queda con la familia posicional correcta y `profile_review_required=true`; no se inventa lateral, mediapunta, extremo o delantero centro.

Especializaciones seguras de esta pasada:

- Ronald Gaspercic, Gert Doumen y Stijn Thijs: portero.
- Davy Oyen y Marc Vangronsveld: lateral izquierdo.
- Suad Katana: líbero, corroborado por fuente especialista.

Los cambios de familia/rol recalculan atributos mediante comparables del mismo sistema histórico; no se aplica ninguna regla 75/25.

## Política histórica de Estados

La pasada consolida el criterio ya utilizado en Turquía: lugar/Estado histórico de nacimiento y nacionalidad futbolística de 1993 son conceptos distintos.

- Katana: `Sarajevo (Yugoslavia)` + identidad Bosnia-Herzegovina; sin `birth_country_id` moderno.
- Bućan: `Split (Yugoslavia)` + identidad Croacia; sin `birth_country_id` moderno.
- Mulavdić: `Gradačac (Yugoslavia)` + identidad Bosnia-Herzegovina; sin `birth_country_id` moderno.

Para Rusia queda escrita como gate explícita la política futura: **URSS no equivale a Rusia**. La pasada rusa deberá separar Estado histórico de nacimiento, ciudadanía/nacionalidad de 1993, selección representada y transliteraciones; nunca se asignará automáticamente un Estado sucesor moderno.

## Fotos e identidad

Los 23 registros quedan enlazados con BDFutol individual y sincronizados entre `created_players_registry.json` y `bdfutbol_photo_queue.json`. Se marcan `ready_for_download` cuando no existe ya una imagen normalizada; no se fabrica una URL de retrato.

## Siguiente frente

Continúa Bélgica, en este orden:

**Waregem 23/20 → Lommel 21/21 → RFC Liège → Cercle Brugge → Oostende → KV Mechelen → Gent → Lierse.**

Rusia permanece congelada hasta terminar esta secuencia belga.
