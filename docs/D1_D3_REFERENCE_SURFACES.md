# D1–D3 · Superficies de referencia

Checkpoint: `0.9.1-d1-d3-reference-surfaces`

## Por qué se rehacen

La modernización R1–R10 eliminó el aspecto retro y ordenó la arquitectura, pero las capturas de 0.9.0 mostraron una deuda de producto: las superficies seguían pareciendo una aplicación administrativa. Había demasiadas tarjetas equivalentes, grandes espacios muertos y poca capacidad para convertir la profundidad del motor en identidad futbolística visible.

D1–D3 fija dos pantallas de referencia antes de propagar el nuevo lenguaje al resto del juego.

## D1 · Dirección de producto

- Moderno y futbolístico, no retro.
- La época vive en fotografías, escudos, estadios, competiciones, reglas y datos, no en cromado antiguo.
- Menos cajas equivalentes y más composición editorial.
- La información de decisión aparece antes que la información contable.
- Texto de interfaz nunca por debajo del suelo de 11 px; el objetivo de las nuevas superficies es 13–14 px para lectura habitual y 11–12 px sólo para metadatos.
- La profundidad debe ser perceptible sin exigir abrir una pantalla estadística secundaria.

## D2 · Ficha de jugador

La ficha principal ahora responde, en este orden, a: quién es, dónde juega, qué le hace distinto, cómo encaja y cuál es su situación.

Incluye:

- cabecera de identidad con club, dorsal, nacionalidad, arquetipo, jerarquía, disponibilidad y fotografía histórica compacta;
- nivel actual sin duplicar la misma valoración mediante estrellas y etiquetas redundantes;
- pulso de encaje táctico, forma, moral, jerarquía, valor y contrato;
- identidad futbolística y rasgos recuperados de la fuente;
- mapa de posiciones con los `Rol1…Rol18` reales y aptitud por rol;
- motivos de encaje táctico;
- mejores recursos del jugador;
- contribución de temporada;
- situación de vestuario y deseo de salida;
- acceso progresivo a atributos, temporada, contrato, médico, trayectoria e informe.

La ficha no debe volver a ser “foto + media + barras”. `ui-quality.mjs` protege los marcadores estructurales de esta composición.

## D3 · Club como centro futbolístico

La pantalla del club deja de organizarse alrededor de consejo y economía. Su primera vista presenta:

- identidad del club mediante estadio, escudo y contexto de competición;
- posición, puntos, forma y situación deportiva;
- siguiente rival;
- once actual sobre el campo;
- formación y plan táctico del usuario;
- bajas y tensiones;
- cuatro futbolistas de referencia con acceso directo a su ficha;
- entrenador de partida como contexto histórico;
- consejo, identidad institucional y economía en la columna secundaria.

### Entrenador histórico y usuario

`source_manager` representa al entrenador asociado al club en la fuente. Cuando el usuario controla ese equipo no se presenta como el entrenador activo: aparece explícitamente como “Entrenador al inicio / referencia histórica”. El plan táctico activo procede del usuario.

### Contexto de estadio

El snapshot de carrera expone también `venue`, recuperado del catálogo fuente, para que estadio y aforo sean parte de la identidad de club y del contexto futbolístico.

## Validación de este checkpoint

- `test_football9394_d1_d3_product_context.py`: 2/2 PASS.
- Web API + catálogo fuente + entrenadores: 25/25 PASS.
- `check:sfc`: PASS.
- `check:ui`: PASS con contrato D1–D3.
- `check:vue`: 23/23 PASS.
- Build Vite: no certificada en este entorno porque no está disponible el binario `vite`; los gates Node previos sí pasan.

## Qué no se declara cerrado

D4–D9 siguen abiertos. Estas dos pantallas son la referencia que debe guiar Inicio, Plantilla, Mercado, Tácticas, previa, directo, postpartido, competiciones y el mundo con rostro. No se considera que toda la interfaz haya alcanzado todavía esta calidad.
