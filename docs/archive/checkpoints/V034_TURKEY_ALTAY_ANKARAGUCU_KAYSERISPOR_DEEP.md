# v0.34 · Altay, Ankaragücü y Kayserispor a profundidad completa

## Punto de partida correcto

Esta tanda parte de `0.33.0-turkey-gaziantep-next-profiles`, no de 0.32. Gaziantepspor ya estaba cerrado 26/26 en 0.33 y Altay, Ankaragücü y Kayserispor sólo tenían siete perfiles de alta confianza adelantados.

## Resultado

- Turquía mantiene 419 jugadores activos.
- Altay: 27/27 perfiles revisados.
- Ankaragücü: 27/27 perfiles revisados.
- Kayserispor: 27/27 perfiles revisados.
- Perfiles tratados en esta tanda: 81; 74 son nuevas profundizaciones respecto a 0.33.
- Perfiles turcos únicos profundizados en la fase: 269.
- Correcciones funcionales de rol respecto a 0.33: 48; acumulado de la fase: 168.
- Posición exacta respaldada por fuente especialista/federativa: 31/81.
- Posición sólo amplia (`Defender`, `Midfielder`, `Forward`) y por tanto especialidad pendiente: 50/81.
- Fechas de nacimiento pendientes: 194 → 124.
- Nacionalidades internacionales pendientes: 193 → 121.
- País de nacimiento pendiente: 323 → 259.
- Altura pendiente: 360 → 344.
- Peso pendiente: 407 → 402.
- Dos perfiles sólo tienen año de nacimiento documentado; no se inventa 1 de enero.
- Retratos BDFutbol nuevos y físicamente empaquetados: 15.
- Retratos BDFutbol normalizados acumulados: 69.
- Biografías 1993-94 actualizadas en los 81 perfiles.

## Posición: precisión antes que relleno

La posición amplia de BDFutbol no se convierte automáticamente en una especialidad. Cuando sólo está demostrado `Defender`, `Midfielder` o `Forward`, el motor recibe un rol neutral de esa línea para funcionar, pero el perfil conserva `profile_position_precision=broad_only`, `profile_review_required=true` y `exact role unresolved`. Las biografías también respetan esa incertidumbre: un defensa amplio se describe como “Defensa”, no como “Defensa central”.

Entre los casos con especialidad corroborada están Orhan Üstündağ (central), Ahmet Akuygur (lateral derecho), Toprak Kırtoğlu (lateral derecho), Tahir Karapınar (interior izquierdo), Şeyhmus Suna (lateral derecho), Ramazan Mahmut Torunoğlu (delantero centro), Sergei Gusev (delantero centro), Yuriy Shelepnytskyi (mediocentro defensivo), Ilian Iliev (mediapunta), David Mitchell (delantero centro), Hayati Soydaş (lateral derecho), Sergey Agashkov (mediocentro), Mukhsin Mukhamadiev (delantero centro), Hakan Kutlu (líbero), Ekrem Onuk (mediapunta), Nexhat Shabani (delantero centro) y los porteros documentados en las fichas individuales.

## Fechas, nacionalidades y países históricos

Se separan nacionalidad futbolística y país histórico de nacimiento. En nacidos en la antigua URSS o Yugoslavia no se fuerza retrospectivamente un `birth_country_id` moderno: el lugar queda documentado en texto como `(USSR)` o `(Yugoslavia)` y la nacionalidad internacional se almacena por separado.

Dos conflictos se dejan expresamente trazados:

- Öztürk Tanrıbilir: BDFutbol/Kayserispor registra 19/05/1966, mientras la ficha oficial TFF y otra fuente biográfica convergen en 03/05/1966. Se conserva 03/05/1966 por prioridad federativa.
- Sergei Yevgenovich Gusev: BDFutbol registra 07/07/1967, mientras Transfermarkt y varias fichas de carrera convergen en 01/07/1967. Se conserva 01/07/1967 y el conflicto queda anotado en el perfil.

Hüseyin Gün (1975) y Ensar Hacımustafaoğlu (1973) sólo tienen año de nacimiento demostrado. `birth_date` permanece nulo y se guarda `historical_birth_year_only`; no se fabrica día ni mes.

## Fotos

Se añaden 15 retratos BDFutbol verificados de los tres clubes. Todos se convierten a JPEG RGB 40×55 mediante recorte centrado y sólo se marca `bundled_normalized_bdfutbol` después de comprobar físicamente el archivo final. El total acumulado pasa de 54 a 69.

## Integridad y QA

- Registro y cola de fotos: 2.107 identidades, IDs únicos y conjuntos sincronizados.
- Cada cambio funcional de rol conserva la valoración global y rematerializa atributos usando comparables originales 1993-94 de la misma línea posicional.
- Los 50 roles amplios se marcan como pendientes de especialización en vez de aceptar la heurística anterior.
- Las biografías canónicas `historical_biography_1993_94` se regeneran después de los cambios y respetan la precisión real de la posición.
- Regresión histórica seleccionada: 80/80 pruebas verdes, incluyendo el bloque específico 0.34 (6/6).
- No se declara ejecutada la suite completa del repositorio.
- No se usa ninguna regla 75/25: no pertenece a Míster 93/94.

## Siguiente frente

Continuar Turquía con Zeytinburnuspor, Karabükspor, Karşıyaka y Sarıyer, intentando llevar los 124/121 huecos actuales a un residuo realmente irresoluble y añadiendo retratos en la misma pasada. Después aplicar la misma profundidad club a club a Bélgica y, con prioridad especial, Rusia.
