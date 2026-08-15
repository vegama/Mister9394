# Bloque 01 — Fundamentos del juego

Estado: implementado en checkpoint 0.3.1.

## Alcance

Este bloque ejecuta M0 + M1 + M2 y abre M3.

### M0 · Rendimiento

- Calendarios de liga cacheados por temporada/competición/participantes.
- Fuerza de club cacheada mientras no cambie la plantilla.
- Ligas de fondo usan `fast_background_v1`: simulación determinista por fuerza, sin construir actas ni aplicar desarrollo individual a miles de jugadores en cada jornada.
- La liga controlada y los partidos explícitamente jugables siguen usando el motor detallado.
- La recuperación diaria sólo reconstruye el índice de plantillas cuando una lesión cambia de no disponible a disponible.

Benchmark del mismo domingo de mundo, Real Sociedad y seeds equivalentes:

| Operación | 0.3.0 | 0.3.1 |
|---|---:|---:|
| Crear carrera | ~0,523 s | ~0,529 s |
| Continuar 1993-10-23 → 1993-10-24 | ~1,092 s | ~0,110 s |

El coste inicial ligeramente superior crea la capa de mánager; la operación repetida cientos de veces cae alrededor de un 90 %.

### M1 · Nueva carrera

- Se mantienen las ligas regulares realmente controlables.
- Cada club muestra plantilla, nivel medio del núcleo, mejores jugadores, socios, presupuesto, deuda y estadio cuando existen en la fuente.
- Escudos y estadios históricos se usan como identidad compacta.
- El universo conserva clubes que participan en competiciones aunque no sean seleccionables como empleo inicial.

### M2 · Bandeja del mánager

- Objetivo de consejo calculado por fuerza relativa.
- Confianza evaluable.
- Forma reciente, moral, posición y no disponibles.
- Incidencias de once, contratos y bajas en una bandeja accionable.

### Apertura de M3 · Once persistente

- XI y banquillo forman parte del save.
- Exactamente once titulares, sin duplicados, con portero, pertenecientes al club y disponibles.
- El motor del partido controlado consume el XI guardado, no uno regenerado silenciosamente.
- La selección automática repara la plantilla al crear carrera y al abrir una nueva temporada.

## Fuente 1993.zip

La MDB de `1993/basedatos/basedatos.mdb` se ha usado para verificar el snapshot normalizado. La regeneración da exactamente el mismo corte de runtime: **23 ligas, 5 torneos, 441 clubes y 10.528 jugadores**. De los 441 clubes, 410 están en estructuras domésticas del corte y otros 31 son necesarios para el mundo/competiciones; no se eliminan por no aparecer en el selector de carrera.

No se duplica la MDB en el runtime limpio. De `1993.zip` sólo se extraen los gráficos utilizados por las entidades 93-94:

- 8.921 retratos disponibles para 10.528 jugadores (~84,7 %);
- 441 escudos de clubes;
- 418 fotografías disponibles de estadios activos.

Los retratos fuente son 40×55. La interfaz los usa de forma deliberadamente pequeña; en la ficha se adopta una jerarquía inspirada en managers clásicos como PC Fútbol 7: retrato pequeño arriba a la derecha y ficha densa. No se amplían como hero images.

## Gates del bloque

- Carrera + API dirigidas: PASS.
- Rollover 93-94 → 94-95 → 95-96: PASS.
- Selección persistente y consumida por el motor: PASS.
- Lesionados rechazados en el XI: PASS.
- Objetivo/confianza reales: PASS.
- SFC Vue sin atributos duplicados: PASS.
- `vite build`: sólo se marca como certificado cuando las dependencias npm estén materializadas; el entorno anterior no pudo descargarlas por resolución de red.
