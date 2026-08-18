# v0.32 · Cierre de metadatos históricos y perfiles turcos

## Objetivo

Continuar el frente abierto en 0.31: nacionalidades, nacimientos, biografías, posiciones exactas y fotos de los jugadores recuperados, mientras se cierran estadios y árbitros con evidencia histórica. La política es fuente primero: un dato incierto permanece nulo/amplio/revisable y nunca se rellena para mejorar artificialmente el porcentaje de completitud.

## Resultado de datos

- Activos en las cuatro ligas: 1.813 (Bélgica 406, Turquía 419, Rusia 492, Grecia 496).
- Perfiles turcos curados en 0.32: 162.
- Correcciones posicionales funcionales: 96.
- Biografías históricas regeneradas: 1.813.
- Retratos BDFutbol empaquetados y normalizados: 36.
- Estadios históricos pendientes: 0.
- Árbitros: Bélgica 25 completo; Turquía 34 completo; Rusia 33 completo; Grecia 11/45 como subconjunto documentado.

## Plantillas turcas profundizadas

Fenerbahçe, Samsunspor, Trabzonspor, Bursaspor, Gençlerbirliği y Kocaelispor se cruzan contra plantillas específicas 1993-94. Cuando la fuente sólo dice `Defender`, `Midfielder` o `Forward`, el jugador conserva `profile_review_required=true` y una etiqueta `exact role unresolved`. La posición funcional interna se normaliza sólo para que el motor pueda operar y no se presenta como hallazgo histórico exacto.

Se recuperan cinco identidades de plantilla inicial ausentes del staging de uso liguero: Vedat Emmez (Bursaspor), Serkan Gültang y Sunay Kahraman (Gençlerbirliği), İsmail Ünal y Fevzi Açıkgöz (Kocaelispor). Cada alta usa atributos fijos por comparables originales de la misma línea; no existe ni se introduce una regla 75/25 para fútbol.

## Discrepancias conservadas

- Ace Khuse: 08/09/1963 se adopta por concordancia de BDFutbol y National-Football-Teams; Transfermarkt publica 1968 y la discrepancia queda almacenada.
- Fevzi Açıkgöz: Transfermarkt lo especializa como central con mediocentro defensivo secundario; BDFutbol lo etiqueta como centrocampista. La ficha de temporada usa central como principal y conserva el conflicto.
- Posiciones amplias: no se convierten en lateral/interior/central exacto sin otra fuente.

## Integridad

Después de las correcciones se regeneran comparables y biografías. Cinco perfiles requirieron reparación de vector/comparables en la última pasada; no quedan referencias a comparables borrados. Registro y cola de fotos contienen 2.107 identidades únicas y permanecen sincronizados.

## QA de cierre

Regresión dirigida: 84/84 pruebas verdes sobre catálogo, snapshot/runtime, motor de partido y capas históricas v0.23, v0.24, v0.29, v0.30, v0.31 y v0.32. La suite total del repositorio no se declara ejecutada.

## Próximo frente

Seguir por el resto de clubes turcos para reducir los 227 nacimientos y 226 nacionalidades todavía pendientes; después aplicar la misma profundidad a Bélgica y, especialmente, Rusia. Fotos individuales se incorporan sólo cuando la identidad BDFutbol es inequívoca.
