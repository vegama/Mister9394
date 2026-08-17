# v0.43 — Bélgica: cierre RFC Liège → Cercle → Oostende → KV Mechelen → Gent → Lierse

Checkpoint: `0.43.0-belgium-final-six-deep`.

Esta pasada cierra el frente belga materializado en v0.42 sin tocar la liga rusa. Se han profundizado 136 identidades de temporada: RFC Liège (24), Cercle Brugge (24), Oostende (19), KV Mechelen (24), Gent (25) y Lierse (20).

## Política de datos

- BDFutbol individual es la fuente de identidad, fecha/lugar de nacimiento, posición y medidas cuando están disponibles.
- Una posición amplia (`Defender`, `Midfielder`, `Forward`) se mantiene amplia y queda marcada como rol exacto no resuelto; no se especializa por equilibrio artificial de plantilla.
- Las etiquetas exactas (`Right back`, `Left back`, `Central`, `Goalkeeper`, `Striker`) sí corrigen la inferencia de staging.
- Los perfiles compartidos ya profundizados no se degradan por una etiqueta posterior más amplia. En esta pasada se preservan de forma explícita Flórián Urbán, Thierry Pister y Gunther Schepens.
- Zaire permanece como identidad estatal/futbolística de 1993 (country id 88); la geografía moderna de RD Congo sólo se conserva como texto de fuente.
- Bosnia-Herzegovina y Croacia se conservan como estados independientes válidos en 1993. No se colapsan automáticamente en Serbia/Yugoslavia.
- No se aplica ninguna regla 75/25: sigue siendo un concepto ajeno a Míster 93/94.

## Resultado

- Fechas de nacimiento pendientes en la liga belga: **116 → 0**.
- Nacionalidades pendientes: **107 → 1**. La única restante es Willy Vincent (Royal Antwerp), ya documentado como internacional mauriciano pero sin un country-id de Mauricio verificado en el catálogo; permanece sin inventar identificador.
- País de nacimiento: **137 → 32**; los 32 restantes corresponden principalmente a perfiles cuya fuente individual no publica lugar/país de nacimiento utilizable.
- Altura: **224 → 150**.
- Peso: **310 → 268**.
- Los 136 jugadores quedan enlazados a perfil individual BDFutbol en staging/registry/photo queue.
- La cola belga de profundización queda vacía en `belgium_deepening_queue_v043.json`.

## Rusia

Rusia no se modifica en esta versión. Queda desbloqueada como siguiente frente, manteniendo la política escrita: URSS no equivale a Rusia; en la pasada rusa se separarán lugar de nacimiento histórico, ciudadanía/nacionalidad de 1993, selección representada y transliteraciones.
