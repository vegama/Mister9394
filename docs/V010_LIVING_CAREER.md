# 0.10 · Living Career / memoria futbolística

## Objetivo

Convertir el mundo persistente en una carrera que recuerde **por qué** importan sus resultados. Esta capa no añade burocracia ni modifica medias para fabricar drama: consume hechos que el motor ya produce y los convierte en relaciones, rivalidades, historias, cambios de banquillo y récords persistentes.

## L1 · Rivalidades con memoria

Las rivalidades iniciales parten de `main_rival_id` y `regional_rival_id` recuperados de la MDB. Partidos cerrados, eliminatorias, goleadas y traspasos entre rivales alteran una temperatura limitada a 0–100. Una rivalidad no histórica sólo puede emerger para el club controlado después de encuentros repetidos; no se generan enemistades aleatorias entre clubes IA.

## L2 · Relación mánager–jugador

Cada futbolista del club controlado mantiene confianza persistente. Titularidades, minutos, marginar a una figura, ponerlo en venta, retirarlo del mercado y renovar contrato dejan historial. La confianza se muestra en ficha y afecta las condiciones de renovación: una relación deteriorada eleva el coste de retención; una relación fuerte puede suavizarlo. **La valoración base del jugador nunca se modifica por esta relación.**

## L3 · Historias abiertas, no noticias de relleno

El sistema abre historias únicamente cuando existe una condición de la partida: lucha por el título/supervivencia, racha, figura descontenta, negociación prolongada, rivalidad caliente o cambio de entrenador. Cuando la condición termina la historia se resuelve y pasa al archivo de Historia. Inicio muestra como máximo tres historias activas para evitar saturación.

## L4 · Mercado de entrenadores IA

Cada mes de temporada se compara posición real, expectativa de club y forma reciente. Una presión alta puede terminar en destitución. El sustituto se selecciona entre entrenadores de la MDB con filtro conservador de edad/procedencia y encaje con la plantilla. `manager_assignments` cambia en el save, por lo que el nuevo entrenador altera desde el siguiente partido el perfil táctico, rotación y desarrollo consumido por la IA. Las destituciones se publican como hechos causales y Noticias muestra el mercado de banquillos.

La MDB mezcla ediciones; por eso una contratación generada en carrera conserva provenance `career_generated_from_mdb_manager_pool` y no se presenta como hecho histórico de 1993.

## L5 · Récords e historia de tu etapa

Los partidos oficiales actualizan balance, mayor victoria/derrota, partido más goleador, racha de victorias y racha invicta. Los amistosos de pretemporada no inflan esos récords. Los récords absolutos sobreviven a los rollovers; sólo las rachas actuales se reinician entre temporadas. Hitos relevantes generan noticias y Club/Historia muestran la memoria acumulada.

## Gates

- Living career: 11/11 PASS.
- Carrera normal: 10/10 PASS; rollover 1993-94→1994-95 PASS; rollover repetido 1994-95→1995-96 PASS.
- Web/API: 13/13 PASS.
- D1/D3/D7/D8: 3/3 PASS.
- F1–F8: 14/14 PASS.
- Total dirigido de cierre: 53/53 PASS.
- Frontend: `check:sfc` PASS, `check:ui` living-career PASS, sintaxis Vue 23/23 PASS.
- El bundle Vite de producción continúa siendo un gate separado: el binario `vite` no está materializado en este entorno.
