# R1 — Modern Product Redesign

Checkpoint opened at **0.6.0-r1** · core implementation continued through **0.6.5-r6**

## Decision

The product no longer tries to look like software from 1993. Míster 93/94 is a modern football-management product whose **world, data, rules, assets and sporting context** are historical.

Historical identity remains in club crests, small player portraits, stadium images, competition formats, transfer rules, foreign-player limits, pesetas and the 1993-94 database. Navigation, typography, density, controls and information hierarchy are contemporary.

## Problems confirmed in 0.5.0

- Eleven top-level navigation buttons competed at the same hierarchy and wrapped on narrower desktop widths.
- The main application accumulated visual rules from 0.3.1, 0.4.0 and 0.5.0 instead of owning one design language.
- Important UI copy used 7–10 px sizes in multiple surfaces.
- The player dossier deliberately recreated a classic grey/blue desktop window and therefore clashed with the rest of the manager.
- `Football9394App.vue` carried the shell, career entry, navigation and every workspace in one component.
- Dark green panels, gradients and borders gave almost every block equal visual weight.

## Implemented in this checkpoint

### R1.1 — Product shell

- New persistent dark sidebar with grouped information architecture:
  - Gestión: Inicio, Plantilla, Tácticas, Mercado.
  - Temporada: Competiciones, Calendario, Noticias.
  - Club y mundo: Club, Economía, Selecciones, Historia.
- New fixed top bar with current section, date, matchday/preseason state, pending decisions and a permanently visible Continuar action.
- Responsive collapse to icon navigation and mobile bottom navigation.

### R1.2 — Visual system reset

- Replaced the previous accumulated manager stylesheet instead of adding a new compatibility layer.
- Light neutral workspace and white information surfaces; dark colour is reserved primarily for navigation and football-specific emphasis.
- One spacing, border, radius, shadow and semantic-colour language across the manager.
- Normal data text now sits at 11–13 px or above. A `check:ui` gate rejects sub-11px CSS typography.
- Removed the old grey/blue classic-window palette, bevel treatment and serif player-name treatment.

### R1.3 — Dashboard hierarchy

- Inicio now has an explicit visual order: next match first, team/board state second, decisions and news next, league context alongside them.
- The next match is the dominant card instead of one panel among equals.
- Decision/status areas use calmer neutral surfaces and semantic colour only where it communicates state.

### R1.4 — Player dossier direction

- Player profile is now a modern entity surface.
- Historical portrait remains deliberately small and sharp.
- Club crest, identity, position, nationality and key metrics are kept in a compact header without recreating old desktop chrome.
- Tabs, attributes, season stats, medical information and report cards share the new product grammar.

### R1.5 — Componentisation started

Extracted from the application monolith:

- `CareerSetup.vue`
- `ManagerSidebar.vue`
- `ManagerTopbar.vue`

This is the start of the architectural cleanup. Feature screens will be extracted during the next R1 passes rather than continuing to enlarge the root component.

## Validation

- `npm run check:sfc`: PASS.
- `npm run check:ui`: PASS.
- Vue `<script setup>` syntax scan: PASS.
- `backend/tests/test_football9394_webapp.py`: **13/13 PASS**.
- Full historical/longitudinal suite was not rerun to completion because it exceeds the execution window; the backend was not modified in R1.
- Production Vite build is not certified in this environment because `npm ci` stalls before materialising Vite. This is an environment/dependency issue, not a reported compile failure.

## R1 closure / continuation

The visual-system foundation and shell are now considered implemented. R2–R6 continue the same direction across Inicio, Plantilla, player dossier, Tácticas, live match and Mercado; see `R2_R6_MODERN_CORE_WORKSPACES.md`. Remaining visual islands are tracked under R7, followed by R8 career creation, R9 interaction depth and the R10 Chromium/1080p beta gate.
