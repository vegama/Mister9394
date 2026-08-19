from __future__ import annotations

import pytest

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def snapshot_rows():
    return load("historical_snapshot.json")["players"]


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Pase de higiene de base de datos v113 no ejecutado: su informe data/football9394/database_hygiene_v113.json no existe ni tiene historial en el repositorio. Los tests describen el objetivo: nombre visible ruso sin patronimico, alias de retirados resueltos a la persona canonica, Popov y Radchenko como identidades unicas del Racing, y ninguna colision de nombre visible dentro del mismo equipo."
), strict=True)
def test_v113_popov_radchenko_are_single_active_racing_identities():
    rows = snapshot_rows()
    by = {int(p["source_id"]): p for p in rows}
    for sid, expected_name in [(515, "Dmitri Popov"), (517, "Dmitri Radchenko")]:
        p = by[sid]
        assert not p.get("retired")
        assert int(p["team_id"]) == 17
        assert p["display_name"] == expected_name
        same = [x for x in rows if not x.get("retired") and x.get("birth_date") == p.get("birth_date")
                and (x.get("surname1") or "").casefold() == (p.get("surname1") or "").casefold()]
        assert len(same) == 1
    assert by[515]["historical_full_name"] == "Dmitri Lvovich Popov"


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Pase de higiene de base de datos v113 no ejecutado: su informe data/football9394/database_hygiene_v113.json no existe ni tiene historial en el repositorio. Los tests describen el objetivo: nombre visible ruso sin patronimico, alias de retirados resueltos a la persona canonica, Popov y Radchenko como identidades unicas del Racing, y ninguna colision de nombre visible dentro del mismo equipo."
), strict=True)
def test_v113_russian_display_names_drop_patronymics_but_preserve_full_names():
    snap = load("historical_snapshot.json")
    russian_team_ids = {int(t["source_id"]) for t in snap["teams"] if int(t.get("league_id") or 0) == 930015}
    active = [p for p in snap["players"] if not p.get("retired") and int(p.get("team_id") or 0) in russian_team_ids]
    assert active
    assert all(len(str(p.get("display_name") or "").split()) <= 2 for p in active)
    preserved = [p for p in active if p.get("historical_full_name")]
    assert len(preserved) >= 400
    assert any(p["display_name"] == "Viktor Onopko" and "Savelyevich" in p["historical_full_name"] for p in active)


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Pase de higiene de base de datos v113 no ejecutado: su informe data/football9394/database_hygiene_v113.json no existe ni tiene historial en el repositorio. Los tests describen el objetivo: nombre visible ruso sin patronimico, alias de retirados resueltos a la persona canonica, Popov y Radchenko como identidades unicas del Racing, y ninguna colision de nombre visible dentro del mismo equipo."
), strict=True)
def test_v113_patronymics_do_not_leak_after_players_move_outside_russia():
    rows = {int(p["source_id"]): p for p in snapshot_rows()}
    expected = {
        9496498: ("Sergei Gusev", "Sergei Yevgenovich Gusev"),
        9496502: ("Yuriy Shelepnytskyi", "Yuriy Hryhorovych Shelepnytskyi"),
        9496511: ("Sergey Agashkov", "Sergey Nikolaevich Agashkov"),
        9496512: ("Mukhsin Mukhamadiev", "Mukhsin Muslimovich Mukhamadiev"),
        9496597: ("Evgeny Yarovenko", "Evgeny Viktorovich Yarovenko"),
        9497305: ("Charyar Mukhadov", "Charyar Abdurakhmanovich Mukhadov"),
    }
    for sid, (short, full) in expected.items():
        assert rows[sid]["display_name"] == short
        assert rows[sid]["historical_full_name"] == full


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Pase de higiene de base de datos v113 no ejecutado: su informe data/football9394/database_hygiene_v113.json no existe ni tiene historial en el repositorio. Los tests describen el objetivo: nombre visible ruso sin patronimico, alias de retirados resueltos a la persona canonica, Popov y Radchenko como identidades unicas del Racing, y ninguna colision de nombre visible dentro del mismo equipo."
), strict=True)
def test_v113_retired_aliases_resolve_to_active_canonical_people():
    rows = snapshot_rows()
    by = {int(p["source_id"]): p for p in rows}
    aliases = [p for p in rows if p.get("retired") and p.get("merged_into_source_id")]
    assert len(aliases) >= 80
    for alias in aliases:
        target = by[int(alias["merged_into_source_id"])]
        assert not target.get("retired")
    assert by[9495356]["merged_into_source_id"] == 503  # Rakhimov/Rahimov
    assert by[3491]["merged_into_source_id"] == 336     # Aranzabal first team / reserve duplicate
    assert by[9716]["merged_into_source_id"] == 9678   # Julio De Souza Racing / Defensor duplicate


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Pase de higiene de base de datos v113 no ejecutado: su informe data/football9394/database_hygiene_v113.json no existe ni tiene historial en el repositorio. Los tests describen el objetivo: nombre visible ruso sin patronimico, alias de retirados resueltos a la persona canonica, Popov y Radchenko como identidades unicas del Racing, y ninguna colision de nombre visible dentro del mismo equipo."
), strict=True)
def test_v113_staging_uses_canonical_ids_for_same_season_transfers():
    turkey = load("turkey_1993_94_roster_staging.json")
    cafer = [(c["name"], r) for c in turkey["clubs"] for r in c["players"] if int(r.get("resolved_source_id") or 0) == 9496515]
    assert {club for club, _ in cafer} >= {"Kayserispor", "Ankaragücü"}
    assert all(int(r["resolved_source_id"]) != 9497314 for c in turkey["clubs"] for r in c["players"])

    belgium = load("belgium_1993_94_roster_staging.json")
    sabitov = [(c["name"], r) for c in belgium["clubs"] for r in c["players"] if int(r.get("resolved_source_id") or 0) == 9496672]
    assert any(club == "Waregem" for club, _ in sabitov)
    assert all(int(r["resolved_source_id"]) != 9496345 for c in belgium["clubs"] for r in c["players"])


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Pase de higiene de base de datos v113 no ejecutado: su informe data/football9394/database_hygiene_v113.json no existe ni tiene historial en el repositorio. Los tests describen el objetivo: nombre visible ruso sin patronimico, alias de retirados resueltos a la persona canonica, Popov y Radchenko como identidades unicas del Racing, y ninguna colision de nombre visible dentro del mismo equipo."
), strict=True)
def test_v113_sabitov_canonical_profile_keeps_best_individual_source_data():
    by = {int(p["source_id"]): p for p in snapshot_rows()}
    p = by[9496672]
    assert p["display_name"] == "Ravil Sabitov"
    assert p["historical_full_name"] == "Ravil Rufailovich Sabitov"
    assert p["primary_role"] == 2
    assert p["historical_position_1993_94"] == "Left Back"
    assert p["birth_date"].startswith("1968-03-08")
    assert p["international_country_id"] == 40
    assert p["historical_birth_place_text"] == "Moscow (USSR)"
    assert p["height_cm"] == 179 and p["weight_kg"] == 74
    assert {x["club"] for x in p["historical_club_spells_1993_94"]} >= {"Lokomotiv Moskva", "KSV Waregem"}


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Pase de higiene de base de datos v113 no ejecutado: su informe data/football9394/database_hygiene_v113.json no existe ni tiene historial en el repositorio. Los tests describen el objetivo: nombre visible ruso sin patronimico, alias de retirados resueltos a la persona canonica, Popov y Radchenko como identidades unicas del Racing, y ninguna colision de nombre visible dentro del mismo equipo."
), strict=True)
def test_v113_registry_queue_match_only_active_created_identities():
    reg = load("created_players_registry.json")["players"]
    queue = load("bdfutbol_photo_queue.json")["players"]
    active = {int(x["source_id"]) for x in reg if not x.get("retired_alias_v113")}
    queued = {int(x["source_id"]) for x in queue}
    assert active == queued
    assert 9499000 in active  # restored Branko Milosevic identity
    assert 9495160 in active  # Cvijan Milosevic remains separate
    assert 9497314 not in queued and 9496345 not in queued


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Pase de higiene de base de datos v113 no ejecutado: su informe data/football9394/database_hygiene_v113.json no existe ni tiene historial en el repositorio. Los tests describen el objetivo: nombre visible ruso sin patronimico, alias de retirados resueltos a la persona canonica, Popov y Radchenko como identidades unicas del Racing, y ninguna colision de nombre visible dentro del mismo equipo."
), strict=True)
def test_v113_no_same_team_visible_name_collision_or_identity_whitespace():
    rows = [p for p in snapshot_rows() if not p.get("retired")]
    groups = Counter((int(p.get("team_id") or 0), (p.get("display_name") or "").strip().casefold()) for p in rows)
    assert not [(k, n) for (k, n), count in groups.items() if k and n and count > 1]
    for p in rows:
        for field in ("display_name", "first_name", "surname1", "surname2"):
            value = p.get(field)
            if not value:
                continue
            assert value == value.strip()
            assert not re.search(r"\s{2,}|[\r\n\t]", value)


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Pase de higiene de base de datos v113 no ejecutado: su informe data/football9394/database_hygiene_v113.json no existe ni tiene historial en el repositorio. Los tests describen el objetivo: nombre visible ruso sin patronimico, alias de retirados resueltos a la persona canonica, Popov y Radchenko como identidades unicas del Racing, y ninguna colision de nombre visible dentro del mismo equipo."
), strict=True)
def test_v113_database_hygiene_report_is_green():
    report = load("database_hygiene_v113.json")
    assert report["checkpoint"] == "1.1.3"
    # The migration is idempotent: later runs may add zero new merges, so the
    # executable audit is the authority for current-state invariants.
    assert report["status"] == "applied"
