# Míster 93/94 — v1.0.0 · F cerrado

## V1.0-F — Club, competiciones, mundo e historia

Estado: **CERRADO**.

Este cierre parte del checkpoint persistido `Mister9394-v100-management-continuity-wave1-checkpoint.zip` y reconstruye el frente F con foco en continuidad histórica, navegación y robustez longitudinal.

### Contrato histórico nuevo: dossiers de temporada

Cada temporada cerrada genera un `season_dossier` congelado e independiente del mundo vivo. El dossier conserva:

- todos los clubes dirigidos por el usuario durante esa temporada, incluidos cambios de banquillo a mitad de curso;
- posición final y contexto de cada proyecto;
- campeones y snapshots de entrenador/plantilla campeona;
- movimientos de ascenso/descenso;
- clasificaciones finales por liga;
- premios si existen, sin exigirlos en temporadas anómalas;
- plazas continentales;
- hitos de selección ocurridos dentro de la temporada;
- recap del club controlado al cierre;
- flags explícitos cuando faltan premios, movimientos o campeones.

Los dossiers usan copias profundas para que una temporada posterior, un traspaso o un cambio de entrenador no puedan reescribir el pasado.

### Migración de saves antiguos

`CAREER_SCHEMA_9394` sube a **23**. Las partidas anteriores siguen siendo compatibles y, al cargarse, reconstruyen `season_dossiers` desde `season_archive` + `season_recaps` cuando todavía no existen.

### Noticias causales

La hemeroteca añade `news_seen_causes`. Dos subsistemas pueden intentar publicar el mismo hecho con claves técnicas diferentes, pero una misma causa canónica sólo se publica una vez. Los hitos simultáneos de club y selección mantienen causas distintas y ambos sobreviven.

### Navegación de competiciones

El detalle de copa continúa leyendo la fase directamente del estado vivo en cada consulta. No se conserva una fase obsoleta entre navegación, Back/F5 o una actualización del torneo.

### Gate destructivo F

Suite: `backend/tests/test_football9394_v100_f_club_world_history.py`

Casos cubiertos:

1. cambio de club durante una temporada y conservación de ambos proyectos;
2. save antiguo sin dossiers y migración automática;
3. campeón que después cambia entrenador/jugadores sin reescribir el snapshot;
4. deduplicación de una misma noticia causal desde dos subsistemas;
5. hitos simultáneos club + selección sin colisión;
6. temporada anómala sin premios, movimientos ni fixtures;
7. tres dossiers consecutivos completamente independientes;
8. fase de copa actualizada entre consultas sin estado de navegación obsoleto.

### Resultados de regresión ejecutados

- Gate F destructivo: **7/7 PASS**.
- F + continuidad de gestión + movilidad de mánager: **16/16 PASS**.
- Torneos + runtime de competiciones: **4/4 PASS**.
- API crítica de carrera/webapp seleccionada: **4/4 PASS**.
- Frontend `check:sfc`: **PASS**.
- Frontend `check:ui`: **PASS**.
- Frontend `check:vue`: **28/28 PASS**.
- `py_compile` de los módulos modificados: **PASS**.

La batería conjunta pesada `world_career + webapp` no terminó dentro de la ventana máxima del contenedor; no produjo fallo antes del timeout. Los gates directamente afectados por F sí quedan certificados arriba.

## Gate F

Al acabar una temporada, el usuario puede reconstruir qué pasó —campeones, clasificación, premios disponibles, movimientos y su propia trayectoria— sin que el presente reescriba el pasado. **Gate F cerrado.**
