from backend.app.football9394.snapshot_runtime import default_runtime_snapshot
from backend.app.football9394.source_catalog_runtime import default_source_catalog


def test_deep_source_catalog_recovers_entities_skipped_by_legacy_importer():
    catalog = default_source_catalog()
    assert catalog.counts["managers"] == 3199
    assert catalog.counts["tactics"] == 123
    assert catalog.counts["referees"] == 3614
    assert catalog.counts["stadiums"] == 2148
    assert catalog.counts["cities"] == 5402
    assert catalog.counts["regions"] == 312
    assert catalog.counts["continents"] == 6
    assert catalog.counts["countries"] == 222
    assert catalog.counts["roles"] == 18
    assert catalog.counts["player_patterns"] == 24
    assert catalog.counts["generic_injuries"] == 33
    assert catalog.counts["specific_injuries"] == 154
    assert catalog.counts["weighted_names"] == 80997


def test_every_domestic_1993_manager_reference_resolves_to_recovered_manager():
    universe = default_runtime_snapshot()
    catalog = default_source_catalog()
    active_league_ids = {int(row["source_id"]) for row in universe.payload["leagues"]}
    domestic_teams = [team for team in universe.payload["teams"] if team.get("league_id") in active_league_ids]
    # Sube al incorporar las seis ligas del 93-94 -Divizia A, Ekstraklasa,
    # A Grupa, Allsvenskan, Tippeligaen y Superligaen- con sus clubes reales.
    # Solo se activan los que pueden alinear once y tienen estadio en la
    # fuente; el resto queda apuntado en pending_activation.
    assert len(domestic_teams) == 517
    domestic_manager_ids = {int(team["manager_id"]) for team in domestic_teams if isinstance(team.get("manager_id"), int)}
    # Sube con las seis ligas del 93-94 incorporadas.
    assert len(domestic_manager_ids) == 440
    assert not [manager_id for manager_id in domestic_manager_ids if catalog.manager(manager_id) is None]
    all_manager_ids = {int(team["manager_id"]) for team in universe.payload["teams"] if isinstance(team.get("manager_id"), int)}
    assert not [manager_id for manager_id in all_manager_ids if catalog.manager(manager_id) is None]


def test_cruyff_source_profile_and_tactic_geometry_are_recovered():
    universe = default_runtime_snapshot()
    catalog = default_source_catalog()
    barcelona = universe.team(3)
    assert barcelona["name"] == "FC Barcelona"
    manager = catalog.manager_with_tactics(barcelona["manager_id"])
    assert manager["display_name"] == "Johan Cruyff"
    assert manager["primary_tactic"] == "3-4-3 Rombo"
    assert manager["coaching_quality"] == 85
    assert manager["tactics"]["primary"]["name"] == "3-4-3 Rombo"
    assert len(manager["tactics"]["primary"]["role_ids"]) == 11
    assert len(manager["tactics"]["primary"]["positions"]) == 22


def test_every_historical_league_has_a_referee_pool_in_the_source():
    universe = default_runtime_snapshot()
    catalog = default_source_catalog()
    historical_league_ids = {int(row["source_id"]) for row in universe.payload["leagues"]}
    # Sube al incorporar las seis ligas del 93-94 -Divizia A, Ekstraklasa,
    # A Grupa, Allsvenskan, Tippeligaen y Superligaen- con sus clubes reales.
    # Solo se activan los que pueden alinear once y tienen estadio en la
    # fuente; el resto queda apuntado en pending_activation.
    assert len(historical_league_ids) == 33
    assert {league_id for league_id in historical_league_ids if not catalog.referees_for_league(league_id)} == set()
    leagues={int(row["source_id"]):row for row in universe.payload["leagues"]}
    assert leagues[930015]["source_rule_hints"]["referee_pool_size"] == 33
    assert leagues[930057]["source_rule_hints"]["referee_pool_size"] == 34


def test_active_clubs_have_stadium_data_and_spain_has_weighted_name_pool():
    universe = default_runtime_snapshot()
    catalog = default_source_catalog()
    active_teams = [team for team in universe.payload["teams"] if isinstance(team.get("league_id"), int)]
    missing = [team["source_id"] for team in active_teams if catalog.stadium(team.get("stadium_id")) is None]
    assert set(missing) == {
        int(team["source_id"]) for team in active_teams
        if team.get("venue_source_status") == "unresolved_historical_1993_94"
    }
    assert all(team.get("league_id") in {930015,930047,930052,930057} for team in active_teams if int(team["source_id"]) in set(missing))
    pool = catalog.name_pool(11)
    assert len(pool["first_names"]) > 500
    assert len(pool["surnames"]) > 2000


def test_referee_backup_proves_birth_dates_are_not_safe_historical_evidence():
    catalog = default_source_catalog()
    conflicts = [row for row in catalog.payload["referees"] if row.get("birth_date_conflict")]
    assert len(conflicts) == 1064
    # Football parameters are still preserved independently of the conflicting DOB.
    assert all(row.get("league_id") is not None and row.get("quality") is not None for row in conflicts[:100])


def test_venue_context_connects_stadium_city_climate_and_region():
    universe = default_runtime_snapshot()
    catalog = default_source_catalog()
    camp_nou = catalog.venue_context(universe.team(3)["stadium_id"])
    assert camp_nou["name"] == "Camp Nou"
    assert camp_nou["width_m"] == 72
    assert camp_nou["length_m"] == 107
    assert camp_nou["capacity"] == 115000
    assert camp_nou["city"]["name"] == "Barcelona"
    assert camp_nou["climate"] is not None


def test_referee_selection_is_deterministic_and_source_backed():
    from backend.app.football9394.refereeing import referee_for_match
    first = referee_for_match(1, seed=939401)
    second = referee_for_match(1, seed=939401)
    assert first is not None
    assert first == second
    assert first.source_id
    assert first.name
    assert first.yellow_tendency >= 0
