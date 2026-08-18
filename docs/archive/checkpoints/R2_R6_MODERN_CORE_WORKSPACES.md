# R2–R6 — Modern core workspaces

Checkpoint: **0.6.5-r6**

This checkpoint intentionally groups several product-review passes instead of stopping after each screen. The backend simulation and historical rules are not changed here; the work is frontend architecture, interaction hierarchy and visual consistency.

## R2 — Navigation and product shell

- Keeps the new persistent sidebar and top bar as the only application shell.
- Navigation remains grouped by management, season and club/world context instead of presenting eleven equal top-level buttons.
- `Continuar` remains permanently visible and the current date / matchday state stays in the top bar.
- Feature workspaces now begin moving out of `Football9394App.vue`, so the shell no longer has to own every screen implementation.

## R3 — Inicio

`HomeDashboard.vue` is now a first-class workspace.

- The next match is the dominant visual element.
- Team state and board pressure are condensed into an executive status panel.
- Required decisions are visually separated from ordinary news.
- The league table becomes a snapshot rather than another equally weighted dashboard box.
- Actions around the next match remain available directly from the hero surface.

## R4 — Plantilla and player dossier

`SquadWorkspace.vue` and `LineupPitch.vue` replace the previous database-like squad surface.

- Search by player name.
- Filter by specialist position and availability.
- Sort by overall, form, position or name.
- Player identity rows include compact historical portraits without enlarging source images beyond their useful role.
- Availability and position use readable semantic chips.
- Starting-XI selection remains inline and visible.
- The selected XI is shown on an actual football pitch instead of as a vertical list.
- The player dossier keeps its small portrait at the right of the identity header and the positional mini-pitch now actually displays the player's primary role.

## R5 — Tactics and live match

`TacticsWorkspace.vue` and `LiveMatchWorkspace.vue` replace the former prototype surfaces.

### Tactics

- The selected XI is physically placed on the pitch for 4-4-2, 4-3-3, 3-5-2 and 5-3-2.
- Player tokens show shirt number, surname, role and overall when space allows.
- Team instructions explain their meaning instead of exposing unexplained dropdowns.
- Tactical consequences are grouped as a compact impact summary.
- The same plan can still be applied during a live match.

### Live match

- Score and match state have first visual priority.
- Match speed / advance controls live in a dedicated command bar.
- Commentary separates notable events from routine play.
- Match statistics read home-vs-away instead of looking like a generic form.
- Substitutions are contained in a dedicated bench surface with a clear action hierarchy.

## R6 — Transfer market

`MarketWorkspace.vue` turns the market into one continuous workflow:

**search → shortlist → player dossier → select target → build offer → wait/respond → incoming offers**.

- Search and filters stay visible above results.
- Results use compact historical portraits, specialist position, club, overall and value.
- Shortlist state is persistent in the row.
- Selecting a target opens the operation rail without losing the search result context.
- Transfer room and foreign-player quota remain visible while building an offer.
- Active negotiations and incoming offers remain in the same workspace.

## Architecture

The root application now delegates the most important daily surfaces to:

- `HomeDashboard.vue`
- `SquadWorkspace.vue`
- `LineupPitch.vue`
- `TacticsWorkspace.vue`
- `LiveMatchWorkspace.vue`
- `MarketWorkspace.vue`

This is deliberately more than visual cleanup: future changes to these flows no longer require editing the entire application template.

## Validation

- `npm run check:sfc`: **PASS**.
- `npm run check:ui`: **PASS**.
- Vue `<script>` / `<script setup>` JavaScript syntax scan: **16/16 PASS**.
- `backend/tests/test_football9394_webapp.py`: **13/13 PASS**.
- A broader grouped gameplay test run progressed through 27 tests without a reported failure but exceeded the execution window, so it is **not recorded as a completed suite pass** for this checkpoint.
- Production Vite build remains **not certified in this environment** because dependency materialisation leaves an incomplete `node_modules` tree with no Vite binary. No compile pass is claimed.

## Next

R7 is now the next product pass: competitions, economy, club, news, history and calendar must be brought up to the same level. After that: R8 career creation, R9 interaction/keyboard/navigation depth and R10 browser/1080p visual beta gate.
