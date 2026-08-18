# V1.0.0 · Ola 4 — Casos límite encadenados

Esta ola continúa el cierre del bucle Inicio → Plantilla/XI → Táctica → Previa → Partido → Postpartido sin dedicar trabajo a assets.

## Qué se ha corregido

### Segunda amarilla → roja

- `second_yellow_red` cuenta como segunda amonestación y como expulsión en estadísticas longitudinales.
- Se unifica el contrato entre falta normal, diving y registro de rendimiento.
- El expulsado desaparece del once operativo y no puede volver mediante un cambio.
- La expulsión genera la sanción liguera correspondiente y llega a ficha, selección, noticias y siguiente jornada.

### Lesión con los dos cambios agotados

- El motor distingue una lesión de la situación `injury_forced_off` cuando el futbolista no puede continuar.
- Un jugador que no puede continuar deja de participar en las acciones del motor.
- Si quedan cambios, continúa disponible únicamente como jugador que debe ser reemplazado.
- Si los dos cambios están gastados, el equipo juega realmente con diez.
- La serialización del partido conserva este estado para F5/guardado/carga.
- La UI del banquillo explica el motivo y el número real de jugadores que siguen en campo.

### Descanso y táctica

- El descanso continúa siendo un estado estable a 45'.
- Táctica recibe estado/minuto del directo y presenta un contexto específico de descanso.
- Un ajuste aplicado en el descanso permanece en el estado del partido y sigue activo al comenzar la segunda parte.

### Calendario anómalo o vacío

- Nuevo `calendar_context` canónico con estados: `scheduled`, `postponed`, `opponent_pending`, `empty` y `season_complete`.
- Un partido aplazado no se puede abrir como si estuviese disponible.
- Un fixture sin rival confirmado tampoco entra al motor: devuelve un mensaje funcional y explícito.
- Inicio y Calendario explican los estados sin rival/fecha en vez de mostrar una pantalla vacía o inventar un adversario.
- Al terminar la temporada, el calendario indica explícitamente que no quedan jornadas oficiales.

### Una sola verdad para lesiones y sanciones

Se añadió `_controlled_absences_for_fixture()` como fuente común de disponibilidad para el próximo compromiso.

La misma baja se propaga a:

1. Inicio: contador y nombres/motivo en atención de plantilla.
2. Plantilla/XI: estado compacto `LES.` / `SANC.` y bloqueo de selección no legal.
3. Ficha: la sanción ya no queda oculta por un informe médico `Disponible`; muestra motivo y partidos pendientes.
4. Táctica/briefing: bloque `TUS BAJAS`.
5. Previa: bajas conocidas antes del partido.
6. Noticias: lesión o sanción con el jugador afectado.
7. Calendario: número, nombres y estado de las bajas del siguiente fixture.

## Tests añadidos

`backend/tests/test_football9394_v100_destructive_matchday_wave4.py`

- segunda amarilla = segunda cautela + roja + sanción + coherencia longitudinal;
- lesión forzada tras dos sustituciones = equipo con diez;
- táctica cambiada al descanso persiste tras reanudar;
- aplazado y rival desconocido son estados seguros y no arrancan el motor;
- calendario vacío al final de temporada tiene estado explícito;
- lesión de partido comparte historia entre ficha, Inicio, briefing, noticias, selección y calendario.

## Gates ejecutados

- Wave 4 destructiva: **6/6**.
- Wave 3 destructiva: **7/7**.
- Core loop + contexto D7/D8: **4/4**.
- Motor de sustituciones/límite 1993-94 dirigido: **2/2**.
- Total backend dirigido de esta certificación: **19/19**.
- Python compile de los módulos modificados: verde.
- SFC structure: verde.
- UI quality gate: verde, ampliado con contratos Wave 4.
- Vue script syntax: **28/28 SFC**.
- `npm run build`: llega limpio a los tres gates anteriores y se detiene porque el checkpoint no incluye `node_modules/.bin/vite` (`vite: not found`). No se marca como build verde.

## Decisión de cierre del frente

El núcleo Inicio + Plantilla/XI + Táctica + jornada de partido queda en **candidato de cierre funcional B+C+D**. Ya no merece otra ola de features en este punto.

Antes de RC aún quedan dos gates de certificación, no nuevas mecánicas:

- recorrido visual real en Chromium/1080p con F5/Atrás/Adelante y texto grande cuando exista un entorno frontend instalable;
- suite longitudinal/release larga para detectar problemas que sólo aparezcan tras varias jornadas/temporadas.

El siguiente frente productivo puede pasar a Mercado + Staff + Entrenamiento/decisiones delegables, manteniendo este core bajo regresión.

Assets: **0 trabajo en esta ola**.
