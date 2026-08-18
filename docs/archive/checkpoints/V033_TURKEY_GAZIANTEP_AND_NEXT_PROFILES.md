# v0.33 · Gaziantepspor y siguiente capa de perfiles turcos

## Objetivo

Continuar el frente de 0.32 club a club: reducir nacimientos y nacionalidades pendientes, corregir posiciones exactas, enlazar perfiles individuales y aumentar retratos históricos sin inventar precisión. El primer objetivo de la tanda es cerrar Gaziantepspor y comenzar Altay, Ankaragücü y Kayserispor sólo con correcciones de alta confianza.

## Resultado

- Jugadores activos en Turquía: 419 (sin altas nuevas en esta tanda).
- Perfiles profundizados en 0.33: 33.
- Gaziantepspor: 26/26 perfiles curados.
- Siguiente capa de alta confianza: 7 perfiles (Altay 2, Ankaragücü 3, Kayserispor 2).
- Correcciones funcionales de rol en la tanda: 24.
- Acumulado de esta fase turca: 195 perfiles curados y 120 correcciones de rol.
- Fechas de nacimiento pendientes en Turquía: 227 → 194.
- Nacionalidades internacionales pendientes: 226 → 193.
- País de nacimiento pendiente: 354 → 323.
- `profile_review_required`: 22 → 30, porque ocho posiciones sólo pueden demostrarse de forma amplia.
- Retratos BDFutbol nuevos: 18.
- Retratos BDFutbol empaquetados acumulados: 54.
- Biografías regeneradas: 1.813; cambiadas respecto a 0.32: 33.

## Correcciones de mayor impacto

Gaziantepspor deja de depender de la asignación heurística del staging inicial. Entre otros cambios:

- İhsan Okay → interior izquierdo; BDFutbol lo etiqueta ampliamente como defensa y el conflicto se conserva.
- Mustafa Özer → lateral derecho.
- Kemal Sönmez → central.
- Hasan Çelik → delantero centro.
- Kubilay Toptaş → delantero centro; BDFutbol lo presenta de forma amplia como centrocampista y la especialización de temporada queda documentada.
- Teboho Claude Moloi → centrocampista con rol exacto todavía pendiente.
- Tayfun Yungul → mediocentro.
- Mehmet Gönülaçar → delantero centro, conservando la discrepancia con la categoría amplia de BDFutbol.
- Mustafa Yücedağ → mediapunta.

En los casos en que la fuente sólo demuestra `Defender`, `Midfielder` o `Forward`, el motor usa una posición neutral de esa línea, pero la ficha queda marcada `exact role unresolved` y `profile_review_required=true`.

## Altay / Ankaragücü / Kayserispor

Primera pasada de alta confianza:

- Ahmet Akuygur → lateral derecho.
- Yuriy Shelepnytskyi → mediocentro defensivo.
- Mehmet Yıldırım → delantero centro.
- Yuriy Matveev → delantero centro.
- Charyar Abdurakhmanovich Mukhadov → delantero centro.
- Öztürk Tanrıbilir → portero.
- Cafer Aydın → delantero centro.

Para Shelepnytskyi y Matveev se conserva el lugar de nacimiento en la URSS en texto y se deja `birth_country_id=null`; no se reescribe retrospectivamente su país de nacimiento como Ucrania/Rusia. La nacionalidad internacional se mantiene separada.

## Fotos

Se normalizan 18 retratos BDFutbol adicionales a JPEG RGB 40×55 con recorte centrado. El estado `bundled_normalized_bdfutbol` sólo se establece cuando el archivo final existe y pasa la comprobación de formato/tamaño. El total del proyecto sube a 54 retratos BDFutbol físicamente empaquetados.

## Integridad

- Registro y cola de fotos: 2.107 filas cada uno, IDs únicos y conjuntos idénticos.
- Todas las correcciones de rol que cambian línea o especialidad regeneran atributos conservando la valoración global y usando comparables originales de la misma línea.
- Ningún comparable de los 33 perfiles tocados apunta a una identidad inexistente ni a otra línea posicional.
- Las 1.813 biografías se regeneran desde el staging después de aplicar las correcciones.
- No se usa ninguna regla 75/25; pertenece al proyecto de baloncesto y no a Míster 93/94.

## QA

- Pruebas específicas v0.33: 8/8.
- Regresión histórica seleccionada v0.23→v0.33: 71/71.
- No se declara ejecutada toda la suite del repositorio.

## Siguiente frente

Continuar la profundización completa de Altay, Ankaragücü y Kayserispor, no sólo los siete casos ya corregidos; después seguir con Zeytinburnuspor, Karabükspor, Karşıyaka y Sarıyer. El objetivo inmediato es llevar los 194/193 huecos turcos restantes a cero o a un conjunto pequeño de identidades realmente irresolubles, incorporando retratos al mismo tiempo.
