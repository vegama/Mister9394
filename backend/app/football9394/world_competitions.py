from __future__ import annotations

"""Shared runtime dispatcher for every certified 1993-94 competition.

This is product code rather than a certification script so world careers and
QA execute exactly the same competition implementations.
"""

from time import perf_counter

from .competition_runtime import build_simple_source_league
from .snapshot_runtime import default_runtime_snapshot
from .source_rules import audit_snapshot_competitions
from .pyramid_activation import audit_competition_activation
from .special_league_runtime import simulate_apsl_1993, simulate_jleague_1993
from .netherlands_runtime import simulate_netherlands_1993_94
from .italy_runtime import simulate_italy_1993_94
from .spain_runtime import simulate_spain_1993_94
from .argentina_runtime import simulate_argentina_1993_94
from .mexico_runtime import simulate_mexico_1993_94
from .colombia_runtime import simulate_colombia_1993
from .brazil_runtime import simulate_brazil_serie_a_1993
from .europe_runtime import (
    simulate_champions_league_1993_94,
    simulate_uefa_cup_1993_94,
    simulate_cup_winners_cup_1993_94,
)
from .spain_cup_runtime import simulate_copa_del_rey_1993_94
from .pyramid_floor import active_pyramid_floors, apply_closed_floor_to_output


def simulate_runtime_competitions(*, seed_offset: int = 0) -> dict:
    universe = default_runtime_snapshot()
    competition_rows = universe.competitions()
    audit = audit_snapshot_competitions(competition_rows)
    activation, pyramids = audit_competition_activation(competition_rows, audit)
    # Certification and career activation are different gates. Every source row
    # marked simulation_ready must execute here, including standalone leagues;
    # activation policy is reported separately and may remain conservative until
    # promotion/relegation destinations exist in the historical universe.
    ready = [entry for entry in audit if entry.simulation_ready]
    outputs = []
    started = perf_counter()
    netherlands = None
    spain = None
    italy = None
    for entry in ready:
        key = entry.ref.key
        t0 = perf_counter()
        if key == ("league", 120):
            season = simulate_apsl_1993(seed_base=1209394 + seed_offset)
            outputs.append({
                "source_key": "league:120", "name": entry.ref.name, "country": entry.ref.country,
                "ok": True, "format": "apsl", "regular_matches": len(season.regular_matches),
                "postseason_matches": 3, "clubs": len(season.regular_table),
                "champion_team_id": season.champion_team_id, "seconds": perf_counter()-t0,
            })
        elif key == ("league", 47):
            season = simulate_brazil_serie_a_1993(universe=universe, seed_base=479394 + seed_offset)
            outputs.append({
                "source_key": "league:47", "name": entry.ref.name, "country": entry.ref.country,
                "ok": season.simulated_matches == 254 and len(season.relegated_team_ids) == 8
                      and len(season.first_phase_tables) == 4 and len(season.second_phase_tables) == 2,
                "format": "bra_serie_a_1993", "matches": season.simulated_matches, "clubs": 32,
                "participant_team_ids": tuple(sorted({row.team_id for table in season.first_phase_tables.values() for row in table})),
                "champion_team_id": season.champion_team_id, "runner_up_team_id": season.runner_up_team_id,
                "relegated_team_ids": season.relegated_team_ids,
                "data_repair_players": season.repaired_players,
                "source_repair_club_ids": season.source_repair_club_ids, "seconds": perf_counter()-t0,
            })
        elif key == ("league", 111):
            season = simulate_jleague_1993(seed_base=1119394 + seed_offset)
            contingency = 1 if season.suntory.winner_team_id == season.nicos.winner_team_id else 0
            outputs.append({
                "source_key": "league:111", "name": entry.ref.name, "country": entry.ref.country,
                "ok": True, "format": "jleague_split", "regular_matches": 180,
                "postseason_matches": 2 + contingency, "clubs": len(season.suntory.table),
                "champion_team_id": season.champion_team_id, "seconds": perf_counter()-t0,
            })
        elif key in (("league", 1), ("league", 2), ("league", 3), ("league", 10), ("league", 11), ("league", 9), ("tournament", 88)):
            if spain is None:
                spain = simulate_spain_1993_94(seed_base=119394 + seed_offset, universe=universe)
            segunda_b = spain.segundab
            if key == ("league", 1):
                outputs.append({
                    "source_key": "league:1", "name": entry.ref.name, "country": entry.ref.country,
                    "ok": spain.primera_matches == 380 and len(spain.primera_table) == 20
                          and len(spain.promoted_to_primera) == len(spain.relegated_to_segunda)
                          and len(spain.promotion_ties) == 2,
                    "format": "spanish_full_pyramid", "regular_matches": spain.primera_matches,
                    "promotion_matches": spain.primera_segunda_playoff_matches,
                    "clubs": len(spain.primera_table), "champion_team_id": spain.primera_table[0].team_id,
                    "promoted_team_ids": spain.promoted_to_primera,
                    "relegated_team_ids": spain.relegated_to_segunda, "seconds": perf_counter()-t0,
                })
            elif key == ("league", 2):
                outputs.append({
                    "source_key": "league:2", "name": entry.ref.name, "country": entry.ref.country,
                    "ok": spain.segunda_matches == 380 and len(spain.segunda_table) == 20
                          and len(segunda_b.relegated_from_segunda) == 4,
                    "format": "spanish_full_pyramid", "regular_matches": spain.segunda_matches,
                    "clubs": len(spain.segunda_table), "champion_team_id": spain.segunda_table[0].team_id,
                    "relegated_team_ids": segunda_b.relegated_from_segunda,
                    "promoted_to_primera": spain.promoted_to_primera,
                    "promoted_from_segundab": segunda_b.promoted_to_segunda, "seconds": perf_counter()-t0,
                })
            elif key[0] == "league":
                table = segunda_b.group_tables[key[1]]
                movement = next(m for m in segunda_b.group_movements if m.source_id == key[1])
                outputs.append({
                    "source_key": f"league:{key[1]}", "name": entry.ref.name, "country": entry.ref.country,
                    "ok": len(table) == 20 and all(row.played == 38 for row in table),
                    "format": "segunda_b_group", "regular_matches": 380,
                    "shared_promotion_matches": segunda_b.promotion_matches,
                    "shared_survival_matches": len(segunda_b.permanence_matches),
                    "clubs": len(table), "group_champion_team_id": table[0].team_id,
                    "promoted_team_ids": segunda_b.promoted_to_segunda,
                    "direct_or_forced_relegated": movement.direct_relegated_team_ids,
                    "forced_reserve_relegated": movement.forced_reserve_relegated_team_ids,
                    "seconds": perf_counter()-t0,
                })
            else:
                outputs.append({
                    "source_key": "tournament:88", "name": entry.ref.name, "country": entry.ref.country,
                    "ok": segunda_b.promotion_matches == 48 and len(segunda_b.promoted_to_segunda) == 4
                          and len(segunda_b.permanence_matches) == 3,
                    "format": "segunda_b_promotion", "regular_feeder_matches": segunda_b.regular_matches_segundab,
                    "promotion_matches": segunda_b.promotion_matches, "survival_matches": len(segunda_b.permanence_matches),
                    "promoted_team_ids": segunda_b.promoted_to_segunda,
                    "relegated_to_tercera": segunda_b.relegated_to_tercera,
                    "seconds": perf_counter()-t0,
                })
        elif key == ("league", 128):
            season = simulate_colombia_1993(seed_base=1289393 + seed_offset, universe=universe)
            apertura_ok = all(len(group) == 8 and all(row.played == 14 for row in group) for group in season.apertura_groups)
            finalizacion_ok = len(season.finalizacion_table) == 16 and all(row.played == 30 for row in season.finalizacion_table)
            aggregate_ok = len(season.aggregate_table) == 16 and all(row.played == 44 for row in season.aggregate_table)
            semifinals_ok = all(len(group) == 4 and all(row.played == 6 for row in group) for group in season.semifinal_groups)
            final_ok = len(season.final_table) == 4 and all(row.played == 6 for row in season.final_table)
            outputs.append({
                "source_key": "league:128", "name": entry.ref.name, "country": entry.ref.country,
                "ok": season.official_matches == 388 and season.bonus_allocation_matches == 4
                      and apertura_ok and finalizacion_ok and aggregate_ok and semifinals_ok and final_ok,
                "format": "col_apertura_finalizacion_quadrangulars",
                "official_matches": season.official_matches,
                "bonus_allocation_matches": season.bonus_allocation_matches,
                "simulated_matches": season.simulated_matches,
                "clubs": len(season.aggregate_table),
                "champion_team_id": season.champion_team_id,
                "runner_up_team_id": season.runner_up_team_id,
                "relegated_team_id": season.relegated_team_id,
                "data_repair_players": season.repaired_players,
                "data_repair_team_ids": season.repaired_team_ids,
                "historical_data_complete": season.repaired_players == 0,
                "seconds": perf_counter()-t0,
            })
        elif key == ("league", 40):
            season = simulate_mexico_1993_94(seed_base=409394 + seed_offset, universe=universe)
            groups_ok = len(season.group_tables) == 4 and all(len(group) == 5 for group in season.group_tables)
            outputs.append({
                "source_key": "league:40", "name": entry.ref.name, "country": entry.ref.country,
                "ok": season.regular_matches == 380 and groups_ok
                      and 0 <= len(season.reclassification_ties) <= 2
                      and len(season.quarterfinal_ties) == 4
                      and len(season.semifinal_ties) == 2
                      and season.postseason_matches == 14 + 2 * len(season.reclassification_ties),
                "format": "mex_group_liguilla_quotient",
                "regular_matches": season.regular_matches,
                "reclassification_matches": 2 * len(season.reclassification_ties),
                "liguilla_matches": 14,
                "postseason_matches": season.postseason_matches,
                "clubs": len(season.regular_table),
                "champion_team_id": season.champion_team_id,
                "runner_up_team_id": season.runner_up_team_id,
                "relegated_team_id": season.relegated_team_id,
                "seconds": perf_counter()-t0,
            })
        elif key == ("league", 16):
            season = simulate_argentina_1993_94(seed_base=169394 + seed_offset, universe=universe)
            apertura_ok = len(season.apertura_table) == 20 and all(row.played == 19 for row in season.apertura_table)
            clausura_ok = len(season.clausura_table) == 20 and all(row.played == 19 for row in season.clausura_table)
            relegation_ok = len(season.relegated_team_ids) == 2 and len(set(season.relegated_team_ids)) == 2
            outputs.append({
                "source_key": "league:16", "name": entry.ref.name, "country": entry.ref.country,
                "ok": season.matches == 380 and apertura_ok and clausura_ok and relegation_ok,
                "format": "arg_apertura_clausura", "regular_matches": season.matches,
                "clubs": len(season.apertura_table),
                "apertura_champion_team_id": season.apertura_champion_team_id,
                "clausura_champion_team_id": season.clausura_champion_team_id,
                "championship_playoffs": season.championship_playoffs,
                "relegated_team_ids": season.relegated_team_ids,
                "seconds": perf_counter()-t0,
            })
        elif key in (("league", 4), ("league", 102)):
            if italy is None:
                italy = simulate_italy_1993_94(seed_base=49394 + seed_offset, universe=universe)
            if key[1] == 4:
                table = italy.serie_a_table
                outputs.append({
                    "source_key": "league:4", "name": entry.ref.name, "country": entry.ref.country,
                    "ok": italy.serie_a_matches == 306 and len(italy.relegated_from_serie_a) == 4
                          and len(italy.promoted_from_serie_b) == 4,
                    "format": "italy_serie_a_b_pyramid", "matches": italy.serie_a_matches,
                    "rounds": 34, "clubs": len(table), "season_end_playoffs": len(italy.serie_a_playoffs),
                    "champion_team_id": table[0].team_id, "relegated_team_ids": italy.relegated_from_serie_a,
                    "promoted_from_serie_b": italy.promoted_from_serie_b, "seconds": perf_counter()-t0,
                })
            else:
                table = italy.serie_b_table
                outputs.append({
                    "source_key": "league:102", "name": entry.ref.name, "country": entry.ref.country,
                    "ok": italy.serie_b_matches == 380 and len(italy.promoted_from_serie_b) == 4,
                    "format": "italy_serie_a_b_pyramid", "matches": italy.serie_b_matches,
                    "rounds": 38, "clubs": len(table), "season_end_playoffs": len(italy.serie_b_playoffs),
                    "champion_team_id": table[0].team_id, "promoted_team_ids": italy.promoted_from_serie_b,
                    "relegated_team_ids": italy.relegated_from_serie_b, "seconds": perf_counter()-t0,
                })
        elif key in (("league", 31), ("league", 54)):
            if netherlands is None:
                netherlands = simulate_netherlands_1993_94(seed_base=319394 + seed_offset, universe=universe)
            if key[1] == 31:
                table = netherlands.eredivisie_table
                regular_matches = netherlands.eredivisie_matches
                movement = {
                    "direct_relegated_team_id": netherlands.direct_relegated_team_id,
                    "relegated_team_ids": netherlands.relegated_team_ids,
                }
            else:
                table = netherlands.eerste_table
                regular_matches = netherlands.eerste_matches
                movement = {
                    "direct_promoted_team_id": netherlands.direct_promoted_team_id,
                    "promoted_team_ids": netherlands.promoted_team_ids,
                    "period_winners": netherlands.period_winners,
                }
            outputs.append({
                "source_key": f"league:{key[1]}", "name": entry.ref.name, "country": entry.ref.country,
                "ok": regular_matches == 306 and netherlands.playoff_matches == 24
                      and len(netherlands.promoted_team_ids) == len(netherlands.relegated_team_ids),
                "format": "netherlands_nacompetitie", "regular_matches": regular_matches,
                "postseason_matches": netherlands.playoff_matches, "clubs": len(table),
                "champion_team_id": table[0].team_id, **movement, "seconds": perf_counter()-t0,
            })
        elif key == ("tournament", 1):
            season = simulate_champions_league_1993_94(universe=universe, seed_base=1939401 + seed_offset)
            outputs.append({
                "source_key": "tournament:1", "name": entry.ref.name, "country": "UEFA",
                "ok": season.simulated_matches == 27 and len(season.group_tables) == 2
                      and len(season.knockout_ties) == 3,
                "format": "uefa_ec_group_stage_1993_94", "matches": season.simulated_matches,
                "start_stage_clubs": len(season.start_stage_team_ids),
                "champion_team_id": season.champion_team_id, "runner_up_team_id": season.runner_up_team_id,
                "data_repair_players": season.repaired_players, "seconds": perf_counter()-t0,
            })
        elif key == ("tournament", 2):
            season = simulate_uefa_cup_1993_94(universe=universe, seed_base=1939402 + seed_offset)
            outputs.append({
                "source_key": "tournament:2", "name": entry.ref.name, "country": "UEFA",
                "ok": season.simulated_matches == 30 and len(season.knockout_ties) == 15,
                "format": "uefa_cup_from_r16_1993_94", "matches": season.simulated_matches,
                "start_stage_clubs": len(season.start_stage_team_ids),
                "champion_team_id": season.champion_team_id, "runner_up_team_id": season.runner_up_team_id,
                "data_repair_players": season.repaired_players, "seconds": perf_counter()-t0,
            })
        elif key == ("tournament", 90):
            season = simulate_cup_winners_cup_1993_94(universe=universe, seed_base=1939490 + seed_offset)
            outputs.append({
                "source_key": "tournament:90", "name": entry.ref.name, "country": "UEFA",
                "ok": season.simulated_matches == 61 and len(season.knockout_ties) == 31,
                "format": "uefa_cwc_from_r32_1993_94", "matches": season.simulated_matches,
                "start_stage_clubs": len(season.start_stage_team_ids),
                "champion_team_id": season.champion_team_id, "runner_up_team_id": season.runner_up_team_id,
                "data_repair_players": season.repaired_players, "seconds": perf_counter()-t0,
            })
        elif key == ("tournament", 3):
            season = simulate_copa_del_rey_1993_94(universe=universe, seed_base=39394 + seed_offset)
            outputs.append({
                "source_key": "tournament:3", "name": entry.ref.name, "country": "España",
                "ok": season.simulated_matches > 0 and season.source_eligible_clubs > 0
                      and season.historical_expected_clubs == 160,
                "format": "esp_copa_del_rey_source_pool_1993_94", "matches": season.simulated_matches,
                "source_eligible_clubs": season.source_eligible_clubs,
                "missing_lower_tier_slots": season.missing_lower_tier_slots,
                "champion_team_id": season.champion_team_id, "runner_up_team_id": season.runner_up_team_id,
                "data_repair_players": season.repaired_players, "seconds": perf_counter()-t0,
            })
        else:
            if key[0] != "league":
                raise AssertionError(f"Torneo certificado sin runtime explícito: {key}")
            season = build_simple_source_league(entry.ref.source_id)
            season.play_all(seed_base=939400 + seed_offset + entry.ref.source_id)
            resolution = season.finalize_table(seed_base=1939400 + seed_offset + entry.ref.source_id)
            table = resolution.table
            promoted = tuple(int(table[pos-1].team_id) for pos in season.rules.direct_promotion_places if 0 < pos <= len(table))
            relegated = tuple(int(table[pos-1].team_id) for pos in season.rules.direct_relegation_places if 0 < pos <= len(table))
            outputs.append({
                "source_key": f"league:{entry.ref.source_id}", "name": entry.ref.name, "country": entry.ref.country,
                "ok": season.played_matches == season.total_matches and all(row.played == season.rules.rounds for row in table),
                "format": "round_robin_cycles", "matches": season.played_matches,
                "rounds": season.rules.rounds, "clubs": len(table),
                "season_end_playoffs": len(resolution.playoffs),
                "champion_team_id": int(table[0].team_id) if table else None,
                "promoted_team_ids": promoted, "relegated_team_ids": relegated,
                "seconds": perf_counter()-t0,
            })
    # Career boundary adaptation: when the MDB does not contain a lower active
    # division, the lowest represented league becomes a closed floor. Historical
    # engines remain untouched for QA; only gameplay movement is suppressed.
    floors = active_pyramid_floors(competition_rows)
    source_rows_by_key = {f"{row['kind']}:{int(row['source_id'])}": row for row in competition_rows}
    adapted_outputs: list[dict] = []
    for output in outputs:
        source_row = source_rows_by_key.get(str(output["source_key"]))
        adapted = apply_closed_floor_to_output(output, source_row=source_row, floors=floors) if source_row else dict(output)
        # Ascenso a Segunda contains the historical Segunda-B permanence series.
        # With Segunda B as the represented Spanish floor, those games no longer
        # cause a sporting exit to an unrepresented Tercera.
        if adapted.get("source_key") == "tournament:88" and floors.get("España"):
            old = tuple(adapted.get("relegated_to_tercera") or ())
            adapted["historical_relegation_candidates"] = old
            adapted["relegated_to_tercera"] = ()
            adapted["survival_matches"] = 0
            adapted["relegation_enabled"] = False
            adapted["pyramid_floor"] = True
            adapted["pyramid_floor_reason"] = "segunda_b_is_lowest_represented_spanish_level"
        adapted_outputs.append(adapted)
    outputs = adapted_outputs

    output_by_key = {row["source_key"]: row for row in outputs}
    active_source_keys = {entry.source_key for entry in activation if entry.active}
    active_outputs = [output_by_key[key] for key in active_source_keys if key in output_by_key]
    terminal_exclusions = [entry for entry in activation if not entry.active and entry.reason == "source_not_admitted"]
    unresolved_activation = [entry for entry in activation if not entry.active and entry.reason != "source_not_admitted"]
    return {
        "season": "1993-94",
        "source_competitions": len(audit),
        "pyramid_eligible": sum(entry.pyramid_eligible for entry in activation),
        "active_declared": sum(entry.active for entry in activation),
        "technical_certified": len(ready),
        "ready_declared": len(ready),
        "ready_executed": sum(bool(row["ok"]) for row in outputs),
        "active_executed": sum(bool(row["ok"]) for row in active_outputs),
        "active_source_keys": sorted(active_source_keys),
        "terminally_excluded": len(terminal_exclusions),
        "unresolved_activation": len(unresolved_activation),
        "all_source_rows_closed": len(terminal_exclusions) + sum(entry.active for entry in activation) == len(audit) and not unresolved_activation,
        "all_active_pass": len(active_outputs) == len(active_source_keys) and all(row["ok"] for row in active_outputs),
        "all_ready_pass": all(row["ok"] for row in outputs),
        "pyramid_floors": {country: {
            "lowest_level": floor.lowest_level,
            "league_source_ids": list(floor.league_source_ids),
            "sporting_relegation_enabled": False,
        } for country, floor in sorted(floors.items())},
        "pyramids": {country: {
            "levels": list(state.league_levels),
            "league_source_ids": list(state.league_source_ids),
            "has_pyramid": state.has_pyramid,
            "all_leagues_ready": state.all_leagues_ready,
            "active": state.active,
            "reason": state.reason,
        } for country, state in sorted(pyramids.items())},
        "excluded": [{
            "source_key": entry.source_key, "name": entry.name, "country": entry.country,
            "simulation_ready": entry.simulation_ready, "pyramid_eligible": entry.pyramid_eligible,
            "reason": entry.reason,
        } for entry in activation if not entry.active],
        "competitions": outputs,
        "seconds": perf_counter()-started,
    }


