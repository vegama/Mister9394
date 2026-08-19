from __future__ import annotations

import pytest

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"


def _snapshot():
    return json.loads((DATA / "historical_snapshot.json").read_text(encoding="utf-8"))


def _players_by_id():
    return {int(p["source_id"]): p for p in _snapshot()["players"]}


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Profundidad de plantillas uruguayas a medias: faltan los campos de identidad normalizada (historical_full_name), las altas verificadas no estan activas y Racing y Liverpool siguen con 16 efectivos en vez de 17."
), strict=True)
def test_uruguay_1993_identity_reconciliation_is_preserved():
    players = _players_by_id()
    assert players[9782]["retired"] is True
    assert int(players[9782]["merged_into_source_id"]) == 9718
    assert players[9718]["display_name"] == "Eduardo Jaume"
    assert int(players[9718]["team_id"]) == 404
    assert players[9718].get("surname2") is None
    assert int(players[9715]["team_id"]) == 2341  # Claudio Morena -> Tecos
    assert players[9703]["historical_full_name"] == "Roberto Óscar Suárez"
    assert players[9703]["surname1"] == "Suárez"
    assert players[9703].get("surname2") is None
    assert int(players[9735]["team_id"]) == 997  # Jacinto Cabrera -> Liverpool
    assert int(players[9741]["team_id"]) == 1411  # Luis Barbat -> Independiente Medellin
    assert players[9751]["display_name"] == "Armando Dely Valdés"
    assert players[9751]["broad_position"] == "DEL"
    assert int(players[9751]["primary_role"]) == 17


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Profundidad de plantillas uruguayas a medias: faltan los campos de identidad normalizada (historical_full_name), las altas verificadas no estan activas y Racing y Liverpool siguen con 16 efectivos en vez de 17."
), strict=True)
def test_uruguay_1993_normalized_identity_fields_are_preserved():
    players = _players_by_id()
    assert players[9746]["historical_full_name"] == "Jesús Cono Aguiar Moreira"
    assert players[9746]["birth_date"].startswith("1968-07-19")
    assert players[9749]["historical_full_name"] == "Washington Óscar Rodríguez Secco"
    assert players[9749]["birth_date"].startswith("1970-01-12")
    assert players[9754]["historical_full_name"] == "Claudio Fabián Ciccia Bourdin"
    assert players[9754]["birth_date"].startswith("1972-04-11")


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Profundidad de plantillas uruguayas a medias: faltan los campos de identidad normalizada (historical_full_name), las altas verificadas no estan activas y Racing y Liverpool siguen con 16 efectivos en vez de 17."
), strict=True)
def test_source_backed_uruguay_1993_additions_are_active_once():
    snapshot = _snapshot()
    players = snapshot["players"]
    expected = {
        9499110: ("Euler Correa", 404, "1970-07-20", 1, "DEF"),
        9499111: ("Richard López", 404, "1972-05-09", 8, "MED"),
        9499112: ("Diego Seoane", 404, "1969-01-10", 17, "DEL"),
        9499120: ("Ramón Castro", 997, "1964-06-13", 7, "MED"),
    }
    for source_id, (name, team_id, dob, role, broad) in expected.items():
        rows = [p for p in players if int(p["source_id"]) == source_id]
        assert len(rows) == 1
        row = rows[0]
        assert row["retired"] is False
        assert row["display_name"] == name
        assert int(row["team_id"]) == team_id
        assert row["birth_date"].startswith(dob)
        assert int(row["primary_role"]) == role
        assert row["broad_position"] == broad
        assert row["creation_batch"] == "roster_coverage_v113_uruguay"
        assert row["attribute_source"] == "fixed_same_era_role_level_comparable_v113"
        assert "synthetic" not in str(row.get("external_origin", "")).lower()


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Profundidad de plantillas uruguayas a medias: faltan los campos de identidad normalizada (historical_full_name), las altas verificadas no estan activas y Racing y Liverpool siguen con 16 efectivos en vez de 17."
), strict=True)
def test_uruguay_additions_do_not_create_name_dob_duplicates():
    players = [p for p in _snapshot()["players"] if not p.get("retired")]
    for source_id in (9499110, 9499111, 9499112, 9499120):
        row = next(p for p in players if int(p["source_id"]) == source_id)
        same = [
            p for p in players
            if p.get("display_name") == row.get("display_name")
            and p.get("birth_date") == row.get("birth_date")
        ]
        assert [int(p["source_id"]) for p in same] == [source_id]


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. Profundidad de plantillas uruguayas a medias: faltan los campos de identidad normalizada (historical_full_name), las altas verificadas no estan activas y Racing y Liverpool siguen con 16 efectivos en vez de 17."
), strict=True)
def test_racing_and_liverpool_gain_real_depth_without_padding():
    players = [p for p in _snapshot()["players"] if not p.get("retired")]
    racing = [p for p in players if int(p.get("team_id") or 0) == 404]
    liverpool = [p for p in players if int(p.get("team_id") or 0) == 997]
    assert len(racing) == 17
    assert len(liverpool) == 16
    assert sum(1 for p in racing if p.get("creation_batch") == "roster_coverage_v113_uruguay") == 3
    assert sum(1 for p in liverpool if p.get("creation_batch") == "roster_coverage_v113_uruguay") == 1


def test_progreso_and_huracan_remain_viable_after_reconciliation():
    players = [p for p in _snapshot()["players"] if not p.get("retired")]
    assert sum(1 for p in players if int(p.get("team_id") or 0) == 2359) >= 16
    assert sum(1 for p in players if int(p.get("team_id") or 0) == 2360) >= 16
