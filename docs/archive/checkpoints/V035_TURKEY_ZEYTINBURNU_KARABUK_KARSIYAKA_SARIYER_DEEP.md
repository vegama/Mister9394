# v0.35.0 — Turquía: Zeytinburnuspor, Karabükspor, Karşıyaka y Sarıyer a perfil individual

## Objetivo de la pasada

Continuar exactamente el frente abierto por v0.34 sobre los cuatro siguientes clubes turcos de 1993-94: **Zeytinburnuspor → Karabükspor → Karşıyaka → Sarıyer**. La prioridad es identidad real, fecha/lugar de nacimiento, nacionalidad futbolística, posición histórica con precisión explícita y foto cuando BDFutbol ofrece un retrato verificable. No se crean jugadores nuevos en esta pasada: se profundizan las 102 identidades que ya estaban reconciliadas en el staging histórico.

Fuentes de plantilla 1993-94:

- Zeytinburnuspor: https://www.bdfutbol.com/en/t/t1993-949025.html
- Karabükspor: https://www.bdfutbol.com/en/t/t1993-9410744.html
- Karşıyaka: https://www.bdfutbol.com/en/t/t1993-949026.html?t=seg
- Sarıyer: https://www.bdfutbol.com/en/t/t1993-949024.html

## Resultado

| Club | perfiles profundizados | retratos nuevos |
|---|---:|---:|
| Zeytinburnuspor | 26 | 3 |
| Karabükspor | 27 | 4 |
| Karşıyaka | 25 | 8 |
| Sarıyer | 24 | 5 |
| **Total** | **102** | **20** |

Los 20 retratos quedan normalizados a **40×55 JPEG RGB** y sincronizados entre `created_players_registry.json`, `bdfutbol_photo_queue.json` y `frontend/public/historical9394/players`.

## Cierre de huecos turcos

Antes de v0.35, Turquía tenía 419 jugadores activos y estos huecos de perfil:

- fecha de nacimiento: **124**
- nacionalidad internacional: **121**
- país de nacimiento: **259**
- altura: **344**
- peso: **402**

Después de esta pasada:

- fecha de nacimiento: **23**
- nacionalidad internacional: **19**
- país de nacimiento: **165**
- altura: **330**
- peso: **397**

Por tanto, esta tanda resuelve **101 fechas completas**, **102 nacionalidades internacionales**, **94 países de nacimiento**, **14 alturas** y **5 pesos**. El único perfil de estos 102 sin fecha completa es **Yılmaz Ece**, cuya fuente sólo documenta 1964; se conserva `historical_birth_year_only=1964` y no se fabrica 01/01.

Los 23 huecos de fecha restantes en Turquía incluyen tres casos deliberadamente parciales —Hüseyin Gün (1975), Ensar Hacımustafaoğlu (1973) y Yılmaz Ece (1964)— más 20 identidades todavía sin fecha fiable. Los 19 huecos de nacionalidad restantes pertenecen a otros clubes, no a estos cuatro.

## Posiciones: precisión antes que falsa exactitud

La pasada deja **14 perfiles con rol exacto** y **88 con posición amplia y rol especialista explícitamente pendiente**.

- Portero se considera una demarcación suficientemente exacta.
- **Hakan Ünsal** queda como **Left Back**, porque BDFutbol lo documenta de forma específica.
- **Evgeny Viktorovich Yarovenko** queda como **Centre Back**, corroborado por perfil especialista además del `Defender` amplio de BDFutbol.
- Cuando BDFutbol sólo ofrece `Defender`, `Midfielder` o `Forward`, el motor conserva un rol interno neutro de esa línea, pero el dato se marca `profile_position_precision='broad_only'`, `profile_review_required=true` y `historical_position_1993_94='… (exact role unresolved)'`.

Esto explica que `profile_review_required` suba de 80 a 168: no es una regresión de datos, sino la eliminación de falsa precisión heredada de heurísticas anteriores.

Cuando una corrección de línea de juego cambia el rol interno, los atributos se vuelven a materializar contra comparables reales de esa posición manteniendo el `overall`; **69 perfiles** necesitaron esa corrección en esta tanda. No se usa ninguna regla 75/25 de baloncesto.

## Casos históricos tratados de forma explícita

- **Miralem Ibrahimović**: identidad bosnia; nacimiento en Banovići en 1963 almacenado como `Banovići (Yugoslavia)`, sin atribuir retroactivamente Bosnia-Herzegovina como Estado de nacimiento.
- **Matjaž Cvikl**: nacionalidad eslovena; `Slovenj Gradec (Yugoslavia)` como contexto histórico de nacimiento.
- **Ziya Yıldız / Zijad Švrakić**: se conserva el nombre futbolístico usado en Turquía, nacionalidades Bosnia-Herzegovina + Turquía y nacimiento en `Sarajevo (Yugoslavia)`.
- **Mirza Golubica**: BDFutbol documenta Bosnia-Herzegovina + Serbia; el id legado de Serbia se interpreta con la capa histórica 1993 como República Federal de Yugoslavia y el nacimiento queda `Zenica (Yugoslavia)`.
- **Metin Mert / Detlef Müller**: se usa **Metin Mert** como identidad futbolística visible; la nota de fuente conserva el nombre legal y la doble nacionalidad Turquía + Alemania.
- **Evgeny Yarovenko**: se adopta 17/08/1962 porque BDFutbol y Transfermarkt coinciden, se documenta la discrepancia con fuentes secundarias que dan 1963, y se mantienen Ucrania + Kazajistán como identidades nacionales con nacimiento `Karatau (USSR)`.
- **Salihi Heroll**: BDFutbol aplica un país moderno de nacimiento sin localidad; fuentes de carrera lo identifican como albanés y nacido en Yugoslavia. Se conserva Albania como nacionalidad sin fabricar un Estado sucesor de nacimiento.
- **İbrahim Köseoğlu**: futbolista turco nacido en Bulgaria; nacionalidad deportiva y país de nacimiento se mantienen separados.

## Integridad

- `created_players_registry.json`: **2.107** filas.
- ids únicos: **2.107**.
- registry y photo queue contienen exactamente el mismo conjunto de ids.
- no se crea ninguna identidad nueva en v0.35; por tanto esta pasada no introduce duplicados por creación.
- las 102 biografías de temporada se regeneran con club, posición, datos de aparición disponibles y nacimiento respaldado por fuente.

## Pruebas

Nuevo gate: `backend/tests/test_football9394_v035_turkey_next_four_deep_profiles.py`.

Cobertura del gate:

- 102/102 filas presentes en los cuatro stagings.
- cierre 124→23 de fecha y 121→19 de nacionalidad.
- año parcial sin fecha inventada.
- estados disueltos y dobles nacionalidades.
- alias/identidades históricas.
- Hakan Ünsal y Yarovenko como roles exactos; posiciones amplias permanecen no resueltas.
- 20/20 fotos 40×55 JPEG RGB y sincronización registry/queue.
- 69 correcciones de rol con comparables de la posición resultante.

Regresión turca v0.33 + v0.34 + v0.35: **20/20 PASS**.

La agrupación más amplia v0.31–v0.35 alcanza sus primeras decenas de checks sin fallo, pero excede la ventana de ejecución conjunta; no se etiqueta falsamente como recertificación completa.

## Siguiente frente

Con esta tanda, el bloque turco principal queda suficientemente profundo para cambiar de país. El siguiente orden recomendado es:

1. **Bélgica**: aplicar el mismo patrón de identidad individual + posición precisa cuando exista + fotos.
2. **Rusia**: dedicar la pasada más fuerte, porque es el frente con mayor necesidad de profundidad histórica, desambiguación ex-URSS y nacionalidades 1993.

Los 23/19 huecos residuales turcos quedan auditados y localizados para una pasada final de cierre, sin bloquear el avance a Bélgica/Rusia.
