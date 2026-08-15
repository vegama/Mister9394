from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.app.football9394.team_builder import build_snapshot_team_sheet


def test_real_sociedad_sheet_uses_real_mdb_players():
    universe = default_runtime_snapshot()
    sheet = build_snapshot_team_sheet(universe, 16)
    assert len(sheet.starters) == 11
    assert len(sheet.bench) == 5
    ids = {int(player.id) for player in (*sheet.starters, *sheet.bench)}
    assert ids <= set(universe.players_by_id)
    assert any(player.name == "Kodro" for player in sheet.starters)
    keeper = next(player for player in sheet.starters if player.position == "GK")
    assert keeper.name in {"Alberto", "Biurrun", "González"}
    assert keeper.goalkeeping == keeper.overall


def test_source_formation_changes_position_counts():
    universe = default_runtime_snapshot()
    sheet = build_snapshot_team_sheet(universe, 16, formation="4-3-3")
    positions = [player.position for player in sheet.starters]
    assert positions.count("GK") == 1
    assert positions.count("DF") == 4
    assert positions.count("MF") == 3
    assert positions.count("ST") == 3
