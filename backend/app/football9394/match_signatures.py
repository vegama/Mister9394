from __future__ import annotations

"""P6 · observable individual signatures from the football match model.

The engine already resolves actions through concrete players.  This module turns
those causal events into a compact boxscore that can be persisted and shown to
the manager without adding a second hidden rating system.
"""

from collections import defaultdict
from typing import Any, Iterable


def _player_rows(sheet: Any) -> dict[str, Any]:
    return {str(p.id): p for p in (*sheet.starters, *sheet.bench)}


def _empty(player: Any) -> dict[str, Any]:
    return {
        "player_id": str(player.id), "player_name": str(player.name), "position": str(player.position),
        "goals": 0, "assists": 0, "shots": 0, "shots_on_target": 0,
        "chances_created": 0, "set_piece_chances": 0, "penalties_taken": 0,
        "penalties_scored": 0, "saves": 0, "fouls": 0, "yellow_cards": 0,
        "red_cards": 0, "offsides": 0, "injuries": 0, "second_balls": 0,
    }


def player_match_boxscore(result: Any, home_sheet: Any, away_sheet: Any) -> dict[str, dict[str, dict[str, Any]]]:
    """Build event-derived player stats for both teams.

    Only observable actions are counted.  There is deliberately no fabricated
    tackle/pass count because the coarse 93/94 engine does not resolve every
    touch.  That keeps the boxscore honest and lets future engine detail extend
    the contract without rewriting career history.
    """
    sheets = {str(home_sheet.team_id): home_sheet, str(away_sheet.team_id): away_sheet}
    rows: dict[str, dict[str, dict[str, Any]]] = {}
    for team_id, sheet in sheets.items():
        rows[team_id] = {pid: _empty(player) for pid, player in _player_rows(sheet).items()}

    pending_shooter: dict[str, str] = {}
    for event in result.events:
        team_id = str(event.team_id) if event.team_id is not None else None
        if team_id not in rows:
            continue
        pid = str(event.player_id) if event.player_id is not None else None
        secondary = str(event.secondary_player_id) if event.secondary_player_id is not None else None
        kind = str(event.kind)

        if kind == "chance":
            if pid in rows[team_id]:
                rows[team_id][pid]["chances_created"] += 1
            if secondary in rows[team_id]:
                pending_shooter[team_id] = secondary
        elif kind in {"free_kick_chance", "set_piece_chance"}:
            if pid in rows[team_id]:
                rows[team_id][pid]["set_piece_chances"] += 1
            if secondary in rows[team_id]:
                pending_shooter[team_id] = secondary
            elif pid in rows[team_id]:
                pending_shooter[team_id] = pid
        elif kind == "penalty":
            if pid in rows[team_id]:
                rows[team_id][pid]["penalties_taken"] += 1
                pending_shooter[team_id] = pid
        elif kind == "goal":
            if pid in rows[team_id]:
                row = rows[team_id][pid]
                row["goals"] += 1; row["shots"] += 1; row["shots_on_target"] += 1
                if "penalti" in str(event.detail).lower(): row["penalties_scored"] += 1
            pending_shooter.pop(team_id, None)
        elif kind in {"shot_off"}:
            shooter = pid or pending_shooter.get(team_id)
            if shooter in rows[team_id]: rows[team_id][shooter]["shots"] += 1
            pending_shooter.pop(team_id, None)
        elif kind in {"save", "penalty_saved"}:
            # Save event belongs to the defending team.  The attacker's shot is
            # inferred from the most recent chance on the opposite side only if
            # that side still has a pending shooter.
            if pid in rows[team_id]: rows[team_id][pid]["saves"] += 1
            for attacking_id in sheets:
                if attacking_id == team_id: continue
                shooter = pending_shooter.pop(attacking_id, None)
                if shooter in rows.get(attacking_id, {}):
                    rows[attacking_id][shooter]["shots"] += 1
                    rows[attacking_id][shooter]["shots_on_target"] += 1
        elif kind == "assist" and pid in rows[team_id]: rows[team_id][pid]["assists"] += 1
        elif kind == "foul" and pid in rows[team_id]: rows[team_id][pid]["fouls"] += 1
        elif kind == "yellow" and pid in rows[team_id]: rows[team_id][pid]["yellow_cards"] += 1
        elif kind in {"red", "second_yellow_red"} and pid in rows[team_id]: rows[team_id][pid]["red_cards"] += 1
        elif kind == "offside" and pid in rows[team_id]: rows[team_id][pid]["offsides"] += 1
        elif kind == "injury" and pid in rows[team_id]: rows[team_id][pid]["injuries"] += 1
        elif kind == "second_ball" and pid in rows[team_id]:
            rows[team_id][pid]["second_balls"] += 1
            pending_shooter[team_id] = pid

    return rows


def player_signature(player: Any) -> dict[str, Any]:
    """Describe the observable footprint expected from attributes *and role*.

    A goalkeeper is never labelled a ball-winner just because an imported
    tackling field is noisy; outfield candidates are narrowed by their actual
    squad job, then ranked only by football attributes.
    """
    scores = {
        "finalizador": float(player.finishing) * .48 + float(player.off_ball) * .28 + float(player.anticipation) * .24,
        "creador": float(player.vision) * .42 + float(player.short_pass) * .32 + float(player.creativity) * .26,
        "desborde": float(player.dribbling) * .42 + float(player.pace) * .28 + float(player.technique) * .30,
        "aereo": float(player.heading) * .46 + float(player.jumping) * .34 + float(player.strength) * .20,
        "balon_parado": float(player.free_kicks) * .58 + float(player.penalties) * .22 + float(player.technique) * .20,
        "recuperador": float(player.tackling) * .42 + float(player.marking) * .30 + float(player.work_rate) * .28,
        "portero": float(player.goalkeeping) * .72 + float(player.positioning) * .18 + float(player.anticipation) * .10,
    }
    slot=str(getattr(player,"squad_slot","") or getattr(player,"position","")).upper()
    pos=str(getattr(player,"position","")).upper()
    if slot=="GK" or pos in {"GK","POR","PORTERO"}:
        candidates=("portero",)
    elif slot in {"CB","RB","LB","DF","DEF"} or pos in {"DF","DEF"}:
        candidates=("recuperador","aereo","balon_parado")
    elif slot in {"DM","CM","AM","RM","LM","RW","LW","MF","MED"} or pos in {"MF","MED"}:
        candidates=("creador","desborde","balon_parado","recuperador")
    else:
        candidates=("finalizador","aereo","desborde","balon_parado","creador")
    ordered=sorted(((key,scores[key]) for key in candidates),key=lambda item:(-item[1],item[0]))
    primary,primary_score=ordered[0]
    secondary,secondary_score=(ordered[1] if len(ordered)>1 else sorted(((k,v) for k,v in scores.items() if k!=primary),key=lambda item:(-item[1],item[0]))[0])
    return {"primary":primary,"secondary":secondary,"primary_score":round(primary_score,1),"secondary_score":round(secondary_score,1)}


def match_signature_report(result: Any, home_sheet: Any, away_sheet: Any) -> dict[str, Any]:
    box = player_match_boxscore(result, home_sheet, away_sheet)
    output: dict[str, Any] = {"teams": {}}
    for sheet in (home_sheet, away_sheet):
        tid = str(sheet.team_id); players = _player_rows(sheet)
        rows = []
        for pid, stats in box[tid].items():
            player = players[pid]
            contribution = (
                stats["goals"] * 5.0 + stats["assists"] * 3.0 + stats["chances_created"] * 1.15
                + stats["shots_on_target"] * .55 + stats["saves"] * .42 + stats["second_balls"] * .25
                - stats["red_cards"] * 3.0 - stats["yellow_cards"] * .35
            )
            rows.append({**stats, "signature": player_signature(player), "impact": round(contribution, 2)})
        rows.sort(key=lambda row: (-float(row["impact"]), -int(row["goals"]), row["player_name"]))
        output["teams"][tid] = {"team_name": sheet.team_name, "players": rows}
    return output


def aggregate_match_environment(results: Iterable[Any]) -> dict[str, float]:
    """Small P6 calibration surface used by tests/tools across match samples."""
    matches = list(results)
    if not matches: return {"matches": 0}
    totals = defaultdict(float)
    for result in matches:
        totals["goals"] += result.home.goals + result.away.goals
        totals["shots"] += result.home.shots + result.away.shots
        totals["shots_on_target"] += result.home.shots_on_target + result.away.shots_on_target
        totals["corners"] += result.home.corners + result.away.corners
        totals["fouls"] += result.home.fouls + result.away.fouls
        totals["yellow_cards"] += result.home.yellow_cards + result.away.yellow_cards
        totals["red_cards"] += result.home.red_cards + result.away.red_cards
        totals["penalties"] += sum(1 for e in result.events if e.kind == "penalty")
        totals["injuries"] += sum(1 for e in result.events if e.kind == "injury")
        totals["set_piece_chances"] += sum(1 for e in result.events if e.kind in {"free_kick_chance", "set_piece_chance"})
    n = len(matches)
    return {"matches": n, **{key: round(value / n, 3) for key, value in totals.items()}}
