# v0.42.0 — Belgium: Waregem + Lommel deep profile pass

Bélgica continúa como frente activo. Rusia permanece intacta en este checkpoint.

## Waregem

Se profundizan los **27 futbolistas reales** ya presentes para Waregem 1993-94. El marcador `23/20` era el número de huecos de fecha de nacimiento/nacionalidad, no el tamaño de la plantilla.

Cierre del bloque:

- fecha de nacimiento: **23 → 0**
- nacionalidad/identidad internacional: **20 → 0**
- 27/27 filas enlazadas a perfil individual BDFutbol
- staging, registro y cola de fotos sincronizados

Entre las correcciones posicionales se eliminan inferencias de equilibrio de plantilla que contradecían la fuente individual. Cuando BDFutbol sólo ofrece una familia amplia (`Defender`, `Midfielder`, `Forward`), el perfil queda marcado para revisión en vez de inventar una especialización. Los casos con corroboración especialista segura conservan el rol exacto, como Hendrie Krüzen (extremo izquierdo), Flórián Urbán (mediocentro defensivo) y Sébastien De Meersman (extremo izquierdo).

Raymond Atteveld queda deliberadamente como conflicto de fuentes: BDFutbol lo etiqueta como centrocampista y el dato específico de la temporada de Waregem usado como contraste lo sitúa como central. El rol de temporada se conserva, pero `profile_review_required=true`; el conflicto no se oculta.

## Lommel

Se profundizan los **22 futbolistas reales** ya presentes para Lommel 1993-94. El marcador `21/21` también correspondía a huecos de fecha/nacionalidad.

Cierre del bloque:

- fecha de nacimiento: **21 → 0**
- nacionalidad/identidad internacional: **21 → 0**
- 22/22 filas enlazadas a perfil individual BDFutbol
- staging, registro y cola de fotos sincronizados

Correcciones especialmente importantes:

- Bart Peeters: **portero**, no lateral.
- Daniël Scavone: **defensa central**.
- Frank Machiels: **defensa central**.
- Frank Berghuis: **extremo izquierdo**.
- Marc Hendrikx: **interior/medio izquierdo**.
- Nela N'Ganzadi: vuelve a la familia **delantero** en lugar de mantener una inferencia de extremo.

Las correcciones de rol/familia recalculan atributos con comparables históricos del mismo sistema. No se usa ninguna regla 75/25.

## Impacto global en Bélgica

Tras Waregem + Lommel:

- fecha de nacimiento: **160 → 116** (-44)
- nacionalidad/identidad internacional: **148 → 107** (-41)
- país de nacimiento estructurado: **176 → 137** (-39)
- altura: **250 → 224** (-26)
- peso: **324 → 310** (-14)

El aumento de perfiles `review_required` es intencional: sustituye especializaciones antiguas inferidas por una familia posicional respaldada cuando todavía no existe evidencia suficiente para afirmar el rol exacto.

## Estados históricos: Zaire y URSS

El checkpoint refuerza la separación entre Estado histórico, nacionalidad/ciudadanía de 1993 y etiquetas modernas de las fuentes.

- El id de país `88`, que las fuentes modernas pueden describir como RD Congo, se presenta como **Zaire** en el contexto futbolístico de 1993.
- Ravil Sabitov conserva `Moscow (USSR)` como lugar histórico de nacimiento y **no recibe `birth_country_id=Russia`**. Rusia (`40`) queda únicamente como identidad/c ciudadanía futbolística de 1993.
- La futura pasada de Rusia mantiene el gate: **URSS no equivale a Rusia**; se separarán nacimiento histórico, ciudadanía/nacionalidad de 1993, selección representada y transliteraciones.

## Fotos, duplicados e integridad

Las 49 identidades del bloque quedan vinculadas a su perfil individual de BDFutbol. `created_players_registry.json` y `bdfutbol_photo_queue.json` mantienen el mismo conjunto de **2.118 source IDs únicos**. No se fabrica ninguna URL de retrato: los perfiles sin imagen ya empaquetada quedan listos para el descargador normalizado.

El gate de duplicados del bloque es `exact_name_birthdate_source_profile_gate_v042` para las 47 identidades que se profundizan por primera vez aquí. Jean-Marie Abeels y Laurent Ballenghien ya tenían un perfil profundo exacto de Germinal Ekeren y conservan su gate `v038`; el paso de Waregem añade el segundo spell de club sin degradar la evidencia anterior.

## Siguiente frente

La secuencia queda fijada exactamente así:

**RFC Liège → Cercle Brugge → Oostende → KV Mechelen → Gent → Lierse.**

Rusia permanece congelada hasta terminar esta secuencia belga.
