# V1.0-I — Cierre UX cotidiana

Fecha: 18-08-2026  
Versión: `1.0.0-i`  
Checkpoint: `1.0.0-i-daily-ux-closed`

## Contrato jugable

La pantalla Inicio debe responder en una lectura rápida a cinco preguntas: qué necesita mi decisión, quién está trabajando, en qué estado está, qué ocurrirá después y por qué Continuar puede detenerse.

### Decisiones

Cada `pending_decision` expone `owner`, `status`, `next_step`, `consequence`, `requires_action` y `blocking`. Las interrupciones duras se reservan a decisiones que perderían sentido si el calendario avanzase antes: partido abierto, contraofertas y ofertas entrantes.

### Procesos

`active_processes` presenta scouting activo, negociaciones en espera y recuperaciones médicas como trabajo en curso. Es información contextual, no burocracia: si `requires_action=false`, el usuario sabe que puede seguir avanzando.

### Qué cambió

`recent_changes` recoge cambios personales y accionables de la carrera (scouting, lesiones, sanciones, mercado, consejo, carrera, vestuario, temporada) y proporciona un destino contextual.

### Continuar

`continue_status` expone estado, etiqueta, explicación y destino. Backend y frontend aplican el mismo bloqueo preventivo para que una decisión abierta no quede enterrada detrás de un día avanzado accidentalmente.

### Persistencia de superficie

Se conserva navegación mediante hash + historial del navegador. Mercado conserva filtros y objetivo en `sessionStorage`; V1.0-I añade competición seleccionada, vista de competición y categoría de noticias.

## Evidencia

- `backend/tests/test_football9394_v100_i_daily_ux.py`: contrato de decisión, proceso en curso, bloqueo preventivo y feed de cambios.
- Regresión específica junto a `test_football9394_manager_career.py` y `test_football9394_webapp.py`.
- `frontend/tools/ui-quality.mjs`: contrato estático V1.0-I.
- `node tools/sfc-structure.mjs`: PASS.
- `node tools/vue-script-syntax.mjs`: PASS.
- micro-pasada assets: `docs/v100_i_asset_microbatch_attempt.json`.

## Limitación del entorno de cierre

La suite completa contiene módulos longitudinales que exceden el límite de ejecución disponible. Los bloques rápidos ejecutados terminan verdes. El build Vite no se recompiló porque `npm ci` no puede resolver el registro npm y la caché local carece de `vue-3.5.40.tgz`; los checks de estructura, UI y sintaxis sí se ejecutaron correctamente.
