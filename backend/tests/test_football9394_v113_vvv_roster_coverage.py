from __future__ import annotations

import pytest

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
VVV = 412
EXPECTED = {
    9499100: ("Eugène Hanssen", "1959-01-09", 2, 72),
    9499101: ("Saeed Janfada", "1964-03-21", 2, 71),
    9499102: ("Pieter van Leenders", "1966-12-10", 7, 70),
    9499103: ("Bert Spee", "1966-09-14", 7, 69),
    9499104: ("Eric Teeuwen", "1972-04-06", 3, 66),
    9499105: ("Jaap Geurtjens", "1974-08-09", 3, 63),
    9499106: ("Micky Oestreich", "1969-08-21", 17, 65),
    9499107: ("Erwin Wolter", "1973-04-12", 7, 66),
}


def rows():
    return json.loads((DATA / "historical_snapshot.json").read_text(encoding="utf-8"))["players"]


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. VVV Venlo 1993-94 sigue con 16 jugadores en lugar de 22 y las altas previstas no se llegaron a crear."
), strict=True)
def test_v113_vvv_1993_94_source_backed_roster_is_no_longer_short():
    active = [p for p in rows() if int(p.get("team_id") or 0) == VVV and not p.get("retired")]
    assert len(active) == 22
    assert len(active) >= 18
    by = {int(p["source_id"]): p for p in active}
    for sid, (name, dob, role, overall) in EXPECTED.items():
        player = by[sid]
        assert player["display_name"] == name
        assert str(player["birth_date"]).startswith(dob)
        assert int(player["primary_role"]) == role
        assert int(player["overall"]) == overall
        assert player["creation_batch"] == "roster_coverage_v113_vvv"
        assert player["identity_source_url"].endswith("/seizoenen/1993-1994")
        assert player["attribute_source"] == "fixed_same_era_role_level_comparable_v113"


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. VVV Venlo 1993-94 sigue con 16 jugadores en lugar de 22 y las altas previstas no se llegaron a crear."
), strict=True)
def test_v113_jos_rutten_is_retained_historically_but_not_active_for_vvv_1993_94():
    by = {int(p["source_id"]): p for p in rows()}
    rutten = by[6993]
    assert rutten["display_name"] == "Jos Rutten"
    assert rutten.get("retired") is True
    assert rutten["snapshot_inactive_semantics"] == "historical_row_retained_but_not_active_1993_94_squad"
    assert "1993_94" in rutten["snapshot_inactive_reason"]


@pytest.mark.xfail(reason=(
    "Backlog de contenido, no regresion de codigo: ver docs/CONTENT_BACKLOG_V113.md. VVV Venlo 1993-94 sigue con 16 jugadores en lugar de 22 y las altas previstas no se llegaron a crear."
), strict=True)
def test_v113_vvv_additions_are_not_duplicate_active_people():
    active = [p for p in rows() if not p.get("retired")]
    for sid, (name, dob, _, _) in EXPECTED.items():
        matches = [p for p in active if p.get("display_name") == name and str(p.get("birth_date") or "").startswith(dob)]
        assert [int(p["source_id"]) for p in matches] == [sid]
