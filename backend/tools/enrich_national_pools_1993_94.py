from __future__ import annotations

"""Add real 1993-94-era players to near-functional national-team pools.

The import is deliberately small and evidence-driven. Every candidate is first
reconciled against the entire current player database; ambiguous candidates stop
the import. Missing players are stored under a non-playable Otros-País owner if
their historical club is not part of an active competition.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from backend.app.football9394.identity_reconciliation import reconcile_player_identity
from backend.app.football9394.snapshot_runtime import PRESENTATION_COUNTRIES
from backend.tools.enrich_world_cup_1994 import (
    build_identity_candidate_index,
    clean_text,
    derived_attributes,
    identity_candidate_pool,
    make_container,
    position_fields,
    write_creation_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SNAPSHOT = REPO_ROOT / "data" / "football9394" / "historical_snapshot.json"
DEFAULT_ADDITIONS = REPO_ROOT / "data" / "football9394" / "national_pool_1993_94_additions.json"
DEFAULT_REPORT = REPO_ROOT / "data" / "football9394" / "national_pool_1993_94_enrichment_report.json"


def build_player(row: dict[str, Any], *, team_id: int) -> dict[str, Any]:
    overall = int(row["overall"])
    pos = str(row["position_code"]).upper()
    primary, broad, role_ratings = position_fields(pos)
    return {
        "source_id": int(row["source_id"]),
        "team_id": int(team_id),
        "display_name": row["display_name"],
        "first_name": row.get("first_name") or row["display_name"],
        "surname1": row.get("surname1"),
        "surname2": None,
        "birth_date": f"{row['birth_date']}T00:00:00",
        "birth_country_id": int(row["country_id"]),
        "international_country_id": int(row["country_id"]),
        "preferred_foot": 1,
        "shirt_number": None,
        "primary_role": primary,
        "broad_position": broad,
        "overall": overall,
        "category": min(99, overall + 1),
        "height_cm": None,
        "weight_kg": None,
        "salary": 0,
        "release_clause": 0,
        "contract_start_year": None,
        "contract_end_year": None,
        "loan": False,
        "initially_reserve": False,
        "retired": False,
        "attributes": derived_attributes(overall, pos, f"national-pool-{row['source_id']}"),
        "birth_city_id": 0,
        "naturalized_country_id": None,
        "basque_origin": False,
        "favorite_shirt_number": 0,
        "injury_proneness": 0,
        "progression_mean": 0,
        "fan_affection": 5,
        "academy_team_id": 0,
        "previous_team_id": 0,
        "previous_team_years": 0,
        "buyback_option": 0,
        "role_ratings": role_ratings,
        "hidden_traits": {"individualist": False, "killer_pass": False, "holds_ball": False, "long_shots": False, "cuts_inside": False, "first_time_play": False, "dives": False},
        "identity_source": row.get("identity_source"),
        "identity_source_url": row.get("identity_source_url"),
        "historical_data_source": row.get("identity_source"),
        "attribute_source": "provisional_pending_profile_review",
        "profile_review_required": True,
        "role_detail_source": "verified_historical_broad_position",
        "historical_club_1994": row.get("historical_club_1994"),
        "historical_position_1993_94": row.get("historical_position"),
        "market_container_origin": row.get("country_name"),
        "external_origin": "national_pool_1993_94",
        "creation_batch": row.get("creation_batch") or "national_team_pool_expansion_0.22",
        "verified_national_pool_year": row.get("verified_national_pool_year"),
        "verified_national_pool_1993_94": bool(row.get("verified_national_pool_year") == 1993),
        "verified_era_pool_1993_94": True,
        "source_confidence": row.get("source_confidence"),
        "historical_context": row.get("historical_context"),
    }


def enrich(
    snapshot_path: Path = DEFAULT_SNAPSHOT,
    additions_path: Path = DEFAULT_ADDITIONS,
    report_path: Path = DEFAULT_REPORT,
    *,
    skip_ambiguous: bool = False,
) -> dict[str, Any]:
    """Incorpora convocatorias reales al universo sin duplicar personas.

    ``skip_ambiguous`` cambia qué se hace cuando el reconciliador no puede
    decidir entre varios futbolistas existentes. Abortar el lote entero es lo
    correcto con tandas curadas a mano —una ambigüedad significa que la fuente
    necesita revisión—, pero con lotes grandes de torneos un solo homónimo
    bloquearía a los otros mil. Apartándolos no se crea ni se toca a nadie: el
    dudoso se queda fuera y aparece en el informe para mirarlo a mano, que es
    la opción conservadora entre "inventar un jugador" y "no importar nada".
    """
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    additions = json.loads(additions_path.read_text(encoding="utf-8"))

    # Idempotent rerun: remove only players derived by this batch. Containers are
    # stable shared ownership records and can be reused safely.
    #
    # Con una excepción que costó cara descubrir: un alta de este lote deja de
    # ser desechable en cuanto otra tanda ha trabajado sobre ella. A Yuri Kovtun
    # lo creó el pool de selecciones y después v046 fusionó en su ficha una
    # identidad rusa con su identificador de BDFutbol, sus transliteraciones y su
    # historial de clubes. Borrarlo y recrearlo desde las convocatorias tiraba
    # todo ese trabajo y dejaba a las referencias de v046 apuntando a una ficha
    # desnuda. Quien lleva marcas de curación posterior se queda, y el
    # reconciliador lo tratará como lo que es: alguien que ya existe.
    CURATED_MARKS = (
        "bdfutbol_id", "identity_merge_history", "name_transliterations",
        "duplicate_resolution", "historical_club_spells_1993_94",
        "profile_review_0_23", "verified_data_corrections",
    )
    snapshot["players"] = [
        p for p in snapshot.get("players", [])
        if p.get("external_origin") != "national_pool_1993_94"
        or any(p.get(mark) for mark in CURATED_MARKS)
    ]
    index = build_identity_candidate_index(snapshot.get("players", []))
    teams_by_id = {int(t["source_id"]): t for t in snapshot.get("teams", [])}
    containers_by_country = {int(t.get("country_id") or 0): t for t in snapshot.get("teams", []) if t.get("market_container")}

    # Un identificador que sobrevive a la limpieza de arriba ya no está libre, y
    # puede que ni siquiera siga siendo de quien lo pedía: la ficha 9495160 la
    # creó este lote para Branko Milošević y una tanda posterior fusionó en ella
    # a Cvijan Milošević. Reutilizar el número haría que dos personas
    # compartieran ficha, así que a esas altas se les da uno nuevo y que el
    # reconciliador decida si son alguien que ya está.
    survivors = {int(p["source_id"]): p for p in snapshot.get("players", [])}
    taken = set(survivors) | {int(t["source_id"]) for t in snapshot.get("teams", [])}
    next_free = max(taken) + 1
    reassigned = 0
    # Compartir identificador con un superviviente no basta para ser la misma
    # persona: la ficha 9495160 la creó este lote para Branko Milošević y hoy la
    # ocupa Cvijan Milošević, que es otro. Pero tampoco basta exigir que
    # coincida la fecha, porque las fuentes discrepan en un dígito —Ramiz
    # Mamedov figura como 21 de mayo en una y 21 de agosto en otra— y entonces
    # se duplicaba. Se pide el apellido y, además, o el nombre de pila o la
    # fecha: Branko y Cvijan se separan por el nombre, Mamedov se reconoce por él.
    def same_person(row: dict[str, Any], other: dict[str, Any]) -> bool:
        def key(value: Any) -> str:
            return str(value or "").strip().casefold()

        surname = key(row.get("surname1"))
        if not surname or surname not in key(other.get("surname1")) + " " + key(other.get("display_name")):
            return False
        given = key(row.get("first_name"))
        if given and given in key(other.get("first_name")) + " " + key(other.get("display_name")):
            return True
        return str(row.get("birth_date") or "")[:10] == str(other.get("birth_date") or "")[:10]

    previous_self: dict[int, int] = {}
    for row in additions.get("players", []):
        source_id = int(row["source_id"])
        if source_id not in taken:
            taken.add(source_id)
            continue
        survivor = survivors.get(source_id)
        row["source_id"] = next_free
        if survivor is not None and same_person(row, survivor):
            previous_self[next_free] = source_id
        next_free += 1
        reassigned += 1
        taken.add(int(row["source_id"]))

    resolutions: list[dict[str, Any]] = []
    created = 0
    reused = 0
    ambiguous = 0
    for row in additions.get("players", []):
        country_id = int(row["country_id"])
        anchor = previous_self.get(int(row["source_id"]))
        if anchor is not None:
            player = survivors[anchor]
            player["international_country_id"] = country_id
            player["verified_era_pool_1993_94"] = True
            reused += 1
            resolutions.append({
                "candidate_source_id": int(row["source_id"]),
                "display_name": row["display_name"],
                "country_id": country_id,
                "resolution": "previous_run_of_this_same_addition",
                "confidence": "high",
                "matched_existing_id": anchor,
                "action": "reused_existing",
            })
            continue
        candidates = identity_candidate_pool(
            index,
            display=row["display_name"],
            given=row.get("first_name") or "",
            family=row.get("surname1") or "",
            dob=row.get("birth_date"),
            expected_team=None,
            override=None,
        )
        result = reconcile_player_identity(
            candidates,
            target_display=row["display_name"],
            target_given=row.get("first_name") or "",
            target_family=row.get("surname1") or "",
            target_birth_date=row.get("birth_date"),
            target_country_id=country_id,
        )
        audit = {
            "candidate_source_id": int(row["source_id"]),
            "display_name": row["display_name"],
            "country_id": country_id,
            "compared_against_existing_players": len(snapshot.get("players", [])),
            "resolution": result.resolution,
            "confidence": result.confidence,
            "matched_existing_id": int(result.player["source_id"]) if result.player else None,
            "candidate_matches": [
                {"source_id": c.source_id, "display_name": c.display_name, "score": c.score, "same_dob": c.same_dob, "same_team": c.same_team, "same_country": c.same_country}
                for c in result.candidates
            ],
        }
        if result.resolution == "ambiguous_existing_candidates":
            if not skip_ambiguous:
                raise RuntimeError(f"ambiguous historical identity: {row['display_name']}")
            audit["action"] = "skipped_ambiguous"
            ambiguous += 1
            resolutions.append(audit)
            continue
        if result.player is not None:
            player = result.player
            player["international_country_id"] = country_id
            player["verified_era_pool_1993_94"] = True
            era_sources = player.setdefault("verified_era_pool_sources", [])
            era_source = {"year": row.get("verified_national_pool_year"), "source": row.get("identity_source"), "url": row.get("identity_source_url")}
            if era_source not in era_sources:
                era_sources.append(era_source)
            if row.get("verified_national_pool_year") == 1993:
                player["verified_national_pool_1993_94"] = True
                sources = player.setdefault("verified_national_pool_sources", [])
                source_row = {"year": 1993, "source": row.get("identity_source"), "url": row.get("identity_source_url")}
                if source_row not in sources:
                    sources.append(source_row)
            audit["action"] = "reused_existing"
            reused += 1
            resolutions.append(audit)
            continue

        container = containers_by_country.get(country_id)
        if container is None:
            container = make_container({"country_id": country_id, "name": row["country_name"], "team_code": f"C{country_id}"})
            snapshot["teams"].append(container)
            teams_by_id[int(container["source_id"])] = container
            containers_by_country[country_id] = container
        player = build_player(row, team_id=int(container["source_id"]))
        snapshot["players"].append(player)
        audit.update({"action": "created", "created_source_id": int(player["source_id"]), "team_id": int(container["source_id"]), "team_name": container["name"]})
        created += 1
        resolutions.append(audit)

    snapshot["players"].sort(key=lambda p: int(p["source_id"]))
    snapshot["teams"].sort(key=lambda t: int(t["source_id"]))
    snapshot["national_pool_1993_94_enrichment"] = {
        "status": "complete",
        "batch": additions.get("batch"),
        "candidates": len(additions.get("players", [])),
        "created": created,
        "reused_existing": reused,
        "skipped_ambiguous": ambiguous,
        "reassigned_source_ids": reassigned,
        "identity_policy": "global existing-player comparison; ambiguity blocks creation",
    }
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    registry = write_creation_registry(snapshot)
    report = {
        **snapshot["national_pool_1993_94_enrichment"],
        "created_player_registry_rows": len(registry),
        "resolutions": resolutions,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--additions", type=Path, default=DEFAULT_ADDITIONS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--skip-ambiguous",
        action="store_true",
        help="aparta los homónimos irresolubles en el informe en vez de abortar el lote",
    )
    args = parser.parse_args()
    report = enrich(args.snapshot, args.additions, args.report, skip_ambiguous=args.skip_ambiguous)
    print(json.dumps({k: v for k, v in report.items() if k != "resolutions"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
