# D1–D8 · Football-first product redesign

Checkpoint: `0.9.2-d1-d8-football-first`

## Objetivo

La pasada R1–R10 modernizó la aplicación y F1–F8 profundizó el fútbol. Las capturas de 0.9.0 demostraron que ambas cosas seguían demasiado separadas: el motor sabía más de lo que la interfaz era capaz de hacer sentir. D1–D8 convierte esa profundidad en jerarquía visual y decisiones visibles.

## D1–D3 · superficies de referencia

La ficha de jugador presenta identidad, rol, mapa posicional, encaje táctico, recursos, jerarquía y situación antes que el inventario completo de atributos. La ficha de club se organiza alrededor de posición, siguiente partido, once, plan, figuras y problemas; consejo y economía son contexto secundario. El entrenador fuente del club controlado se etiqueta como referencia histórica, no como técnico activo del usuario.

## D4 · Inicio como jornada

Inicio deja de ser un mosaico de KPIs equivalentes. La primera lectura es: quién eres, contra quién juegas, dónde estás, cómo llegas y qué necesita una decisión. Después aparecen figuras/tensiones, noticias, zona de clasificación, consejo y ritmo de carrera.

## D5 · información por prioridad

Las nuevas superficies reservan el primer nivel para decisión e identidad. Metadatos permanecen en 11–12 px; texto útil y titulares ganan tamaño y espacio. Las pantallas nuevas evitan repetir el mismo concepto mediante número, estrellas y etiqueta simultáneamente.

## D6 · profundidad visible

Plantilla expone encaje agregado del XI, tensiones y riesgo de disponibilidad. Táctica muestra qué futbolistas ejecutan bien o mal el plan y cuáles lo fuerzan. Mercado explica los motivos de encaje táctico del objetivo antes de enviar una oferta.

## D7 · jornada con principio y consecuencia

El directo tiene una previa futbolística con plan rival y amenazas. Al terminar aparece una lectura rápida del resultado y una selección de eventos causales —goles, errores, expulsiones, balón parado y ajustes— antes del relato cronológico completo.

## D8 · mundo con rostro funcional

El partido consume al entrenador rival real de la fuente, su táctica, los tres jugadores de mayor nivel disponibles, el árbitro asignado y el estadio. Estos actores ya no son campos decorativos: ayudan a preparar y entender el encuentro.

El snapshot de partido añade `opponent_context` con `manager`, `tactics` y `key_players`. Árbitro y estadio continúan siendo los mismos perfiles que consume el motor.

## Gates

- D1–D3 context: 2/2 PASS.
- D7–D8 matchday context: 1/1 PASS.
- Regresión dirigida D1–D8/web/fuente/coaching/directo: 30/30 PASS; 7 tests no relacionados fueron excluidos de ese comando.
- `check:sfc`: PASS.
- `check:ui`: PASS con contrato D1–D8.
- `check:vue`: 23/23 PASS.

## D9 · cerrado en 0.9.3

La pasada visual se ha realizado finalmente en Chromium real a 1920×1080 usando los templates Vue y CSS del repo con datos/activos representativos de 1993-94. El navegador detectó y forzó correcciones en Táctica y jornada de partido antes de cerrar el gate.

Resultado: 10/10 superficies sin overflow horizontal, 0 texto visible por debajo de 11 px y acciones críticas de Táctica/previa/directo dentro del primer viewport. Detalle y capturas: `docs/D9_CHROMIUM_VISUAL_GATE.md`.

El bundle Vite sigue siendo un gate técnico separado y no certificado en este entorno porque `vite` no está materializado.
