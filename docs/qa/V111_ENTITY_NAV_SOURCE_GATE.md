# QA gate — v1.1.1 entity navigation / onboarding source closure

Fecha: 18-08-2026

## Alcance

Checkpoint source posterior a la auditoría UX v1.1.0. Cierra navegación contextual de entidades, recuperación/feedback, onboarding contextual y refactor del shell sin declarar todavía RC browser.

## Evidencia

- `Football9394App.vue`: 69.808 bytes; contrato M exige `<70.000`.
- `useEntityNavigation.js`: jugador, club, competición y partido; carga asíncrona serializada, retry y sincronización con URL/history.
- Endpoint `GET /api/football9394/careers/{career_id}/teams/{team_id}` añadido de forma intencional al snapshot de rutas M.
- Ficha de club externo mantiene incertidumbre de scouting (`overall_is_exact=false` cuando corresponde).

## Accesibilidad source añadida

- command palette modal con focus trap y devolución del foco al control que la abrió;
- enlace **Saltar al contenido** visible al recibir foco;
- `main` focalizable como destino semántico;
- error global con `role=alert` y lenguaje de jugador;
- estos contratos quedan protegidos por `check:ux`.

## Gates verdes

- Frontend: version, SFC structure, UI quality, UX product contract y Vue syntax (38/38).
- M refactor: 5/5.
- I daily UX funcional: 4/4; queda fuera del conteo únicamente el sentinel histórico que exige versión literal `1.0.0-i`.
- J match closure: 4/4 mediante ejecución segmentada.
- K management closure: 6/6.
- L emotion/milestones: 6/6.
- Core loop + management continuity: 5/5.
- Team entity endpoint + scouting uncertainty: 2/2.

## No certificado

- `vite build` final.
- render Chromium actual.
- matriz 1920×1080 / 1366×768 / 1280 / 1024 y zoom.
- playtest nuevo/intermedio/hardcore/teclado/destructivo.

Motivo: dependencias npm no materializadas; no existe caché local útil y la descarga queda bloqueada por DNS en este entorno. Un timeout o una imposibilidad de entorno no se contabilizan como PASS.
