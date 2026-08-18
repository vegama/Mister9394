# v0.29 — Perfiles individuales TUR/RUS/GRE y auditoría de extranjeros de Grecia

Este checkpoint profundiza la capa individual de las tres ligas recién activadas sin convertir datos dudosos en hechos. La pasada es curada y trazable: sólo cambia identidad, biografía, posición o vínculo de retrato cuando existe una ficha individual suficientemente clara; cuando una corrección de rol cambia el bloque futbolístico, los atributos se vuelven a materializar desde comparables históricos ya existentes en la base. No se usa la regla 75/25 de Basket Manager.

## Perfiles individuales

Se han revisado 20 perfiles: 9 de Turquía, 6 de Rusia y 5 de Grecia. Diecinueve quedan enlazados a una ficha BDFutbol con retrato verificable y pasan a `ready_for_download`; Vassilis Tsartas conserva su ID de ficha para identidad/biografía, pero permanece en `pending_identity_profile` porque esa ficha no aporta un retrato utilizable.

Correcciones de posición/rol que obligan a recalibrar el vector de atributos:

- Nezih Ali Boloğlu: delantero inferido → portero.
- Kubilay Türkyılmaz: medio inferido → delantero centro.
- Ahmet Bulut: delantero inferido → portero.
- Mustafa Kocabey: delantero genérico → delantero centro.
- Fyodor Cherenkov: defensa inferido → centrocampista.
- Dmitri Ananko: delantero inferido → defensa central.
- Krzysztof Warzycha: extremo inferido → delantero centro.

También se corrigen o completan datos individuales relevantes de Reinhard Stumpf, Mert Korkmaz, Falko Götz, Ali Erdal Keser, Gintaras Staučė, Viktor Onopko, Nikolai Pisarev, Aleksandr Pomazun, Dimitris Saravakos, Vassilis Tsartas, Tasos Mitropoulos y Alexis Alexandris.

Roger Ljung tenía dos identidades: la ya verificada del Mundial y otra creada al importar Galatasaray. Se conserva la identidad verificada `9494093`, se asigna a Galatasaray y se elimina `9496356`. El staging, el audit de Turquía y el registro de fotos apuntan ya al mismo jugador. El proceso es idempotente y no vuelve a crear el duplicado.

La trazabilidad completa queda en `data/football9394/turkey_russia_greece_individual_profile_audit.json`. La cola BDFutbol se regenera a 1.650 identidades y coincide uno a uno con `created_players_registry.json`.

## Límite de extranjeros de Grecia 1993-94

La investigación deja un candidato histórico muy fuerte: **3 extranjeros**. Hay varias piezas independientes que encajan:

1. El expediente Bosman de EUR-Lex documenta el marco UEFA 3+2 adoptado en 1991. Es una fuente jurídica primaria para el marco UEFA, pero no demuestra por sí sola la cláusula doméstica griega de 1993-94.
2. La Ley griega 1958/1991, publicada en el Government Gazette A 122/5-5-1991 y conservada por el Ministerio de Deportes, aporta el marco legal profesional de la época, pero en el texto recuperado no aparece la cláusula numérica específica de la Alpha Ethniki.
3. Nikos Nioplias recuerda expresamente que cada equipo disponía de tres extranjeros en esa época.
4. Novasports registra que el 30 de noviembre de 1988 se instituyó la participación de un tercer extranjero en el campeonato griego.
5. RSSSF documenta una excepción material: los chipriotas no contaban como extranjeros; también señala casos de albaneses con raíces griegas tratados técnicamente como no extranjeros. La excepción chipriota sí queda implementada porque está respaldada de forma explícita y es independiente del número máximo.

Fuentes registradas en el audit:

- EUR-Lex, Case C-415/93 (Bosman): https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:61993CJ0415
- Ministerio de Deportes de Grecia, Ley 1958/1991, FEK A 122/5-5-1991: https://minsports.gov.gr/wp-content/uploads/2012/11/1958_%CE%A6%CE%95%CE%9A_122%CE%91_5-5-91%CE%A4%CE%BC%CE%AE%CE%BC%CE%B1%CF%84%CE%B1_%CE%91%CE%BC%CE%B5%CE%B9%CE%B2%CE%BF%CE%BC%CE%AD%CE%BD%CF%89%CE%BD_%CE%91%CE%B8%CE%BB%CE%B7%CF%84%CF%8E%CE%BD_-_%CE%91%CE%B8%CE%BB%CE%B7%CF%84%CE%B9%CE%BA%CE%AD%CF%82_%CE%91%CE%BD%CF%8E%CE%BD%CF%85%CE%BC%CE%B5%CF%82_%CE%95%CF%84%CE%B1%CE%B9%CF%81%CE%B5%CE%AF%CE%B5%CF%82_%CE%BA%CE%B1%CE%B9_%CE%AC%CE%BB%CE%BB%CE%B5%CF%82_%CE%B4%CE%B9%CE%B1%CF%84%CE%AC%CE%BE%CE%B5%CE%B9%CF%82.pdf
- AthleteStories, entrevista a Nikos Nioplias: https://www.athletestories.gr/nioplias-nikos-me-mia-ball-sta-podia/
- Novasports, tercer extranjero (30/11/1988): https://www.novasports.gr/category/novasportsstorieshd/article/1477326/otan-o-tritos-ksenos-mpike-stin-zwi-mas-video/
- RSSSF, Foreign Players in Greece since 1959/60: https://www.rsssf.org/players/foreign-players-in-grk6080.html

### Decisión de implementación

**No se activa todavía `3` en el runtime.** Falta recuperar el texto primario doméstico —decisión/reglamento de EPO/organizador o FEK aplicable— que fije de forma inequívoca el número para 1993-94.

Sí se ha ampliado el motor con `domestic_equivalent_country_ids`: en competiciones domésticas griegas, Chipre (`country_id=25`) se trata como nacionalidad equiparada, mientras que en competiciones continentales sigue contando por asociación. Es una mejora genérica del motor y no presupone el límite numérico.

Por tanto, el checkpoint conserva `max_foreigners_starting = null` y `max_foreigners_squad = null`, guarda `candidate_limit = 3` como hipótesis fuertemente corroborada y deja un único bloqueo explícito: recuperar la fuente reglamentaria doméstica primaria que demuestre el límite aplicable en 1993-94. Esto evita convertir una inferencia histórica muy plausible en una regla de juego presentada como certeza.

El estado y todas las fuentes quedan en `data/football9394/greece_1993_94_foreign_rule_evidence.json`.
