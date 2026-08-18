# F1–F8 · Football depth closure

Checkpoint: **0.9.0-f1-f8-depth-closed**

The 0.8 source recovery changed the implementation strategy: before inventing a
football property, the game now asks whether the supplied MDB already contains
it. F1–F8 turn that recovered information into gameplay rather than exposing it
as decorative metadata.

## F1 · Footballers with identity — CLOSED

- Rol1…Rol18 source ratings and specialist slots drive lineup fit.
- Source hidden tendencies are consumed by the engine: individualism, killer
  pass, ball retention, long shots, cuts inside, first-time play and diving.
- Source consistency, anticipation, work rate, strength, vision, dribbling,
  off-ball movement, shot power, set pieces and injury proneness reach the
  detailed footballer model.
- Player archetypes are derived from football evidence. Overall remains visible
  and unchanged by the label: the archetype explains a player; it does not
  secretly buff him.

## F2 · Coaches and tactics — CLOSED

- The recovered Entrenador entity is first-class world data.
- AI clubs consume the source coach's primary/attacking/defensive tactic,
  tendency, pressing, rotation and set-piece preference.
- Thirteen era-compatible formation structures are supported by the detailed
  engine and the formation board.
- Coach quality never becomes a flat +X player/team bonus. Positive player
  development is multiplied conservatively by coaching quality, role/tendency
  fit, youth usage, player relationship, source progression and preferred
  player patterns.
- Coach identity affects substitution timing and in-match tactical reactions.
- `manager_assignments` is persisted in the save, so club→coach is world state
  rather than a perpetual lookup against the immutable opening snapshot.
- The human-controlled club has no source-coach bonus: the user is the manager.

Source caveat: coach entities and their attributes come from the supplied MDB;
individual club assignments are marked mixed-edition until historically cured.

## F3 · Football match causality — CLOSED

The text engine now exposes football causes rather than anonymous score rolls:
recovery/possession → creator → chance type → shooter → save/goal/rebound,
plus defensive errors, through balls, combinations, crosses, individual moves,
long shots, penalties, direct free kicks, corners and second balls.

- Match consistency changes execution spread, not base ability.
- Pace/line/offside, pressing/work rate, width, directness and player traits
  interact visibly.
- Source referees alter discipline and remain attached to the match result.
- Source stadium context is attached to detailed/live matches. Pitch dimensions
  and grass quality have deliberately small tactical/physical effects. Climate
  is descriptive geography only; it is not fabricated match-day weather.
- Coach set-piece preference reaches routines without replacing player set-piece
  skill.

The 120-match F8 sample currently produces **2.575 goals/match** against the
Spanish Primera 1993-94 target of **2.603**.

## F4 · Squad hierarchy, tension and medical memory — CLOSED

- Squad roles distinguish Figura, Titular, Promesa, Rotación and Fondo.
- Satisfaction reacts to promised/expected importance, starts, appearances and
  results. Persistent under-use can create a real `wants_move` market state.
- Match injuries now use the 187-definition source injury catalogue. They retain
  diagnosis, body area, laterality, expected return, recurrence flag and
  recovery history instead of collapsing to “Problemas físicos”.
- Availability still uses `injury_days` as a compatibility field for old saves.
- Injury to a selected player remains a surfaced manager decision; the game does
  not silently rewrite the user's XI.

## F5 · Organic market — CLOSED

- Transferability no longer comes from player-id lotteries.
- Signals come from football circumstances: free agent, expiry, reserve status,
  dissatisfaction/exit desire and explicit listing.
- AI recruitment uses specialist squad need, affordability and coach tactical
  fit.
- Rival interest in a user negotiation is generated from clubs that can afford
  the player and need his position rather than a random flag.
- Inferred contracts are deterministic/contextual and explicitly labelled as
  career-inferred.
- Athletic Club eligibility consumes the MDB `OrigenVasco` source flag and its
  own generated academy output instead of surname heuristics.

## F6 · Long career — CLOSED

- Age is calculated from birth date at the current career date.
- Annual age curves can improve young players and progressively reduce physical
  / technical capacity in older players.
- Retirement is persistent and removes the player from active club membership.
- Academy promotions are materialised only to fill real senior-squad gaps, so
  the universe does not gain hundreds of unnecessary senior players every year.
- Newgens use the MDB country-weighted name/surname pools, country surname rules,
  academy quality, actual squad needs and specialist role structure.
- A focused ten-year cohort gate confirms retirements, source-backed academy
  replacement and squad sizes remaining between 18 and 25.
- 1993-94→1994-95 and repeated rollover to 1995-96 are explicitly re-tested.

## F7 · Beauty and usability — CLOSED FOR THIS PASS

R1–R10 remains the product language. F1–F8 adds football depth without creating
new visual grammars:

- squad/market/player dossier surface archetype, traits, tactical fit and squad
  tension;
- the medical tab shows current diagnosis and source-backed history;
- live match shows stadium/city and referee context;
- all thirteen formations render through the common tactics workspace;
- text remains modern/readable; the 1993-94 identity lives in historical
  content, rules, assets and vocabulary rather than retro UI chrome.

## F8 · Realism / fun gate — CLOSED AS AN AUTOMATED DEPTH GATE

`backend/tools/audit_football9394_f1_f8.py` samples 120 Primera fixtures and
requires:

- calibrated goal environment;
- tactical and mentality diversity;
- player-archetype diversity;
- causal chance chains including errors, second balls and set pieces;
- coach tactical adjustments;
- referee discipline;
- source stadium coverage;
- coach set-piece identity.

Current result: every check passes. Automated tests also cover ten-year ageing
and academy replacement, persistent coach assignments and source-backed medical
history.

### What this gate does *not* claim

It is not a substitute for a human “is this fun for ten matches?” playtest and
it is not a new certification of the slow full-world ten-season M15 gate. That
full test exceeded the execution window in this environment during this close
without returning an assertion failure. It had passed in the previous product
checkpoint; for 0.9 it is recorded as **not re-certified in this execution**,
not silently promoted to PASS.

The production Vite/Chromium render is likewise not certified here because the
provided frontend package lacks the `vite` binary. The SFC structure, UI quality
and Vue-script syntax gates all pass before that external dependency failure.
