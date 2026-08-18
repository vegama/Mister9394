# V1.0-L — Emoción e hitos · cierre canónico

Fecha: 18-08-2026  
Checkpoint: `1.0.0-l-emotion-milestones-closed`

## Contrato cerrado

Los momentos importantes tienen peso visual y memoria, pero no crean un segundo motor narrativo ni una cadena de cinemáticas obligatorias. El contrato es:

`hecho canónico → presentación proporcional → archivo congelado → reaparición contextual`

La memoria nunca decide que algo ocurrió: sólo editorializa hechos que ya están guardados por clasificación, palmarés, transición, movilidad del mánager o resultado de partido.

## Hitos canónicos

Se añade `career_milestones.py` como proyección persistente y deduplicada de capítulos de la carrera:

- título del club controlado;
- ascenso o descenso del club controlado;
- cierre de cada temporada;
- cambio de club, regreso, dimisión o destitución;
- partido de rivalidad sólo cuando el calor o la magnitud del resultado justifican recordarlo.

La clave estable de cada hecho evita duplicados por F5, reentrada o reconstrucción de snapshot. La lista es personal y concisa: los campeones del resto del mundo permanecen en Palmarés/Honores, pero no expulsan de la memoria de carrera un título antiguo del usuario.

## Campeones y cierre de temporada

Los honores de liga congelan además subcampeón, puntos del campeón y margen cuando el dato existe, conservando entrenador y plantilla campeona ya archivados. `ChampionsWorkspace` utiliza ese contexto.

`SeasonEndOverlay` muestra el movimiento de categoría y los momentos de la temporada que se convertirán en memoria. Sigue siendo saltable mediante cierre inmediato o `Continuar a la nueva temporada`; se eliminó además una repetición del XI de la temporada.

## Historia y carrera

`HistoryWorkspace` incorpora:

- archivo de hitos canónicos;
- mejor y peor temporada con un score derivado sólo de datos archivados;
- figura y goleador por temporada cuando existen;
- motivos legibles del cierre de cada etapa del mánager;
- mantenimiento del archivo de storylines existente como capa separada.

El dossier de temporada sube a versión 2 y congela los hitos de ese cierre para que el futuro no reescriba el pasado.

## Rivalidades y reencuentros

La previa (`LiveMatchWorkspace`) recibe `opponent_context.history`, rivalidad y reencuentros. Sólo reaparecen hitos realmente relacionados con el club/rival actual, priorizando los enfrentamientos directos sobre recuerdos generales.

## Gates ejecutados

- V1.0-L específico: **6/6 PASS**.
- historia viva + movilidad + historia de club/mundo: **25/25 PASS**.
- V1.0-J Partido: **4/4 PASS**.
- V1.0-K Gestión: **6/6 PASS**.
- V1.0-G longitudinal: **3/3 PASS**.
- soak 3 temporadas (`docs/qa/V100_L_3SEASON_GATE.json`): final `1996-97`, **444 clubes activos**, plantillas 18/22/25 min-mediana-max, **0 cajas negativas**, **3 recaps**, **87 honores**, **3 transiciones**, estado final `healthy`, save 16,52 MB.
- memoria personal tras el soak: **6 hitos**, dos por temporada en el escenario de prueba; los 87 honores globales permanecen fuera de ese stream y por tanto no lo saturan.
- higiene/release V1.0-H: **7/7 PASS**.
- frontend: versión PASS, estructura SFC PASS, calidad UI PASS y sintaxis Vue **28/28 PASS**.
- checkpoint fuente sin `node_modules` ni `frontend/dist`; el build Vite no se declara ejecutado.
- assets: 10.195 fotos conservadas; 4 intentos fallidos por DNS y trazados en `docs/v100_l_asset_microbatch_attempt.json`.

Siguiente frente canónico: **V1.0-M — Refactor progresivo**.
