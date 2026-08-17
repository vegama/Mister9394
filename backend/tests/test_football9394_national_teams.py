from backend.app.football9394.national_teams import national_team_catalog, select_national_squad
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot


def test_source_backed_national_teams_exist_and_select_balanced_squad():
    universe = default_runtime_snapshot()
    catalog = national_team_catalog(universe)
    names = {row.name for row in catalog}
    assert {"España", "Italia", "Brasil", "Argentina", "Alemania"} <= names
    squad = select_national_squad(universe, 11)
    assert len(squad) == 22
    assert len({p["id"] for p in squad}) == 22
    assert sum(p.get("broad_position") == "POR" for p in squad) >= 2
    assert all(p["nationality_id"] == 11 for p in squad)
