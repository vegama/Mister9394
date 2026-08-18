# v0.36.0 — Bélgica: Seraing, Charleroi y Standard a perfil individual + reparación de identidades

## Objetivo de la pasada

Abrir el frente belga después del cierre práctico de Turquía y aplicar ya el criterio fuerte del proyecto: **plantilla histórica completa visible en fuentes, identidad individual, posición real con precisión explícita, nacionalidad/fecha/lugar de nacimiento y foto cuando el retrato puede verificarse**.

Esta tanda trabaja especialmente **FC Seraing, Charleroi y Standard Liège**, y corrige además la identidad de **Donatien Kimoni** en RFC Liège porque la investigación de Standard reveló una colisión de apellido que no podía dejarse pendiente.

Fuentes de temporada principales:

- FC Seraing 1993-94 — BDFutbol: https://www.bdfutbol.com/en/t/t1993-9412101.html
- FC Seraing 1993-94 — Transfermarkt: https://www.transfermarkt.com/rfc-seraing-1996-/kader/verein/54426/saison_id/1993
- Charleroi 1993-94 — BDFutbol: https://www.bdfutbol.com/en/t/t1993-9410718.html
- Charleroi 1993-94 — Transfermarkt: https://www.transfermarkt.com/rsc-charleroi/startseite/verein/172/saison_id/1993
- Standard Liège 1993-94 — BDFutbol: https://www.bdfutbol.com/en/t/t1993-9410012.html
- Standard Liège 1993-94 — Transfermarkt: https://www.transfermarkt.com/standard-luttich/kader/verein/3057/saison_id/1993
- Donatien Kimoni — Transfermarkt: https://www.transfermarkt.co.uk/donatien-kimoni/profil/spieler/939131

## Resultado cuantitativo

- **71 perfiles** belgas revisados/curados en esta tanda.
- **9 identidades históricas nuevas** creadas.
- **2 reutilizaciones de identidad incorrectas reparadas**.
- **37 correcciones de rol** con rematerialización de atributos mediante comparables de la nueva posición, conservando el `overall`.
- **7 posiciones amplias** se dejan deliberadamente como `broad_only` en vez de inventar una especialidad.
- **4 retratos BDFutbol** nuevos quedan incluidos y normalizados a 40×55 JPEG RGB.
- **65 perfiles con id BDFutbol** quedan identificados/encolados para descarga de foto; no se fabrica ninguna imagen cuando la fuente no ha sido recuperada.

Plantillas de staging tras hacer la unión de fuentes:

| Club | Antes | Después |
|---|---:|---:|
| FC Seraing | 19 | **21** |
| Charleroi | 20 | **22** |
| Standard Liège | 24 | **27** |
| RFC Liège | 24 | **24** |

Standard deja de estar artificialmente cortado en Nuyens: la fila liguera de BDFutbol incluye también a **Daniel Marc Kimoni** y **Emmanuel Duah**, y Transfermarkt añade como miembro de plantilla a **Dimitri Habran**.

En Seraing se añaden como miembros de plantilla visibles en Transfermarkt **Harald Heinen** y **Johan Vanheusden**. En Charleroi se añaden **Olivier Desbruyeres** y **Michael Paci**. Para estos cinco jugadores que no están en la tabla liguera BDFutbol usada por el staging, se guardan `0` en los campos estadísticos sólo como ausencia de fila y se marca explícitamente `league_row_absent=true`; su biografía dice que **no se inventan minutos ni apariciones**.

## Reparaciones de identidad

### Edmilson

El importador v0.25 había reutilizado por apellido el `source_id=4929`, **Edmilson Dias Lucena**, cuya identidad original pertenecía al CS Marítimo y cuya fecha de nacimiento es 29/05/1968.

El jugador de Seraing es otra persona: **Edmilson Paulo da Silva**, 16/04/1968, Pernambuco, 176 cm / 76 kg. Se crea como `source_id=9498005`, se conserva el registro liguero de Seraing (31 partidos, 30 titularidades, 2.703 minutos y 15 goles) y Transfermarkt lo sitúa específicamente como **Left Winger**.

El `source_id=4929` vuelve a su `team_id=301` original y se eliminan los metadatos belgas que v0.25 le había adherido.

### Remy

El importador había hecho algo análogo con `source_id=6387`, **Jacques Remy**, procedente del SM Caen.

El jugador de Charleroi 93/94 es **Samuel Remy**, 23/10/1973, Mettet, 178 cm / 71 kg. Se crea como `source_id=9498006`, conserva sus 8 partidos / 382 minutos / 1 gol y queda como **Left Midfield** de acuerdo con la plantilla específica de temporada.

`source_id=6387` vuelve a su `team_id=244` original y deja de contaminar Charleroi.

### Donatien Kimoni ≠ Daniel Marc Kimoni

La investigación de Standard destapó un tercer riesgo de identidad. No se fusionan los dos Kimoni:

- **Donatien Kimoni** (`source_id=9496276`) — RFC Liège, 07/10/1973, Verviers, Bélgica; la fuente consultada sólo precisa **Midfield**, así que queda `broad_only` como centrocampista.
- **Daniel Marc Kimoni** (`source_id=9498007`) — Standard Liège, 18/08/1971 según el perfil individual BDFutbol, Liège, Bélgica, 178 cm / 76 kg; Transfermarkt 93/94 lo sitúa como **Centre-Back**.

Esto evita convertir una coincidencia de apellido en un duplicado/fusión silenciosa.

## Standard: dos filas ligueras recuperadas

La página BDFutbol 93/94 documenta 26 jugadores con participación liguera. Las dos filas que faltaban en staging eran:

- **Daniel Marc Kimoni** — 1 partido, 4 minutos.
- **Emmanuel Duah** — 1 partido, 20 minutos.

Duah queda como `source_id=9498008`, nacido el 14/11/1976 en Kumasi (Ghana), 177 cm / 74 kg, y su posición específica 93/94 es **Left Winger**.

## Fotos incorporadas

Quedan empaquetados cuatro retratos BDFutbol nuevos, todos normalizados a **40×55 JPEG RGB** y sincronizados en registry + queue:

- `9498005.jpg` — Edmilson Paulo da Silva.
- `9498006.jpg` — Samuel Remy.
- `9498007.jpg` — Daniel Marc Kimoni.
- `9498008.jpg` — Emmanuel Duah.

El total de retratos BDFutbol normalizados incluidos en el proyecto pasa de **89 a 93**.

## Cierre de huecos belgas de esta tanda

Antes:

- jugadores activos: **406**
- sin fecha de nacimiento: **330**
- sin nacionalidad internacional: **292**
- sin país de nacimiento: **302**
- sin altura: **362**
- sin peso: **400**

Después:

- jugadores activos: **413**
- sin fecha de nacimiento: **275**
- sin nacionalidad internacional: **248**
- sin país de nacimiento: **268**
- sin altura: **322**
- sin peso: **369**

El activo crece sólo en **+7 netos** pese a crear 9 identidades porque las dos reutilizaciones falsas dejan correctamente la liga belga y vuelven a sus clubes originales.

`profile_review_required` pasa de 0 a 7 porque siete fuentes sólo dan `Defender`, `Midfielder` o equivalente amplio. No es pérdida de información: se elimina falsa precisión y se deja documentado qué falta para cerrar el rol exacto.

## Política histórica aplicada

- Se prefiere la **unión de jugadores visibles en fuentes 93/94** al límite arbitrario de 18.
- No se inventan minutos/partidos para un miembro de plantilla que no aparece en la tabla liguera usada.
- Un apellido coincidente nunca basta para reutilizar una identidad cuando la fecha/perfil contradice la asociación.
- Yugoslavia y URSS se tratan según el contexto de nacimiento real: el lugar puede conservarse como texto histórico sin retroasignar un Estado sucesor moderno.
- Las posiciones amplias permanecen `broad_only` hasta conseguir una fuente especialista.
- Las correcciones de rol rehacen atributos por comparables posicionales manteniendo el nivel del jugador.
- No se usa ninguna regla 75/25 de baloncesto.

## Auditoría y pruebas

Nuevos artefactos:

- `backend/tools/enrich_belgium_profiles_v036.py`
- `backend/tests/test_football9394_v036_belgium_deep_profiles.py`
- `data/football9394/historical_profiles_metadata_audit_v036.json`
- `data/football9394/historical_metadata_gaps_v036.json`
- `data/football9394/historical_biographies_audit_v036.json`
- `data/football9394/belgium_identity_repairs_v036.json`
- `data/football9394/bdfutbol_photo_normalization_v036_belgium.json`

Validación determinista ejecutada en dos bloques disjuntos del módulo 93/94: **78/78 PASS** en el primer bloque transversal y **88/88 PASS** en la cadena histórica v0.23-v0.36, para un total de **166/166** pruebas ejecutadas sin fallo en esos bloques. El subconjunto específico de identidad + v0.35 + v0.36 da además **16/16 PASS**.

Se corrigió también `backend/tools/export_bdfutbol_photo_queue.py`: el regenerador sólo reconocía los gates antiguos y podía omitir 14 identidades válidas creadas en v0.35/v0.36 aunque la cola persistida estuviera correcta. Ahora contempla los gates modernos y vuelve a reconstruir las **2.116** entradas del registry de forma uno-a-uno.

Los antiguos tests que fijaban literalmente `2.107` identidades, `12.499` jugadores de snapshot o `406` belgas se han hecho longitudinales (`>=` + unicidad/integridad de conjuntos) para que una ampliación histórica válida de plantilla no convierta en fallo una mejora posterior.

La tanda de simulaciones longitudinales pesadas no se etiqueta como PASS global porque superó el límite de ejecución del runner antes de finalizar; no se ha usado ese timeout como prueba de corrección.

## Siguiente bloque

Bélgica ya está abierta con el mismo estándar profundo que Turquía, pero todavía conserva **275 fechas** y **248 nacionalidades** por completar en el resto de clubes. El siguiente bloque belga debe continuar esa reducción por clubes hasta cerrar el país; **después** sí merece entrar Rusia con una pasada especialmente fuerte, porque parte de **492 jugadores activos, 465 fechas y 455 nacionalidades pendientes**, con mucha más carga de desambiguación URSS/ex-URSS.
