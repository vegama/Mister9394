from backend.app.football9394.club_signing_policy import club_specific_signing_eligibility
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot


def test_athletic_policy_uses_explicit_mdb_basque_origin_not_name_guessing():
    universe=default_runtime_snapshot()
    athletic_player=universe.player(185)  # Julen Guerrero
    romario=universe.player(9)
    assert club_specific_signing_eligibility(6, athletic_player)[0] is True
    ok, reason=club_specific_signing_eligibility(6, romario)
    assert ok is False
    assert "origen vasco" in reason


def test_other_clubs_do_not_inherit_athletic_specific_policy():
    universe=default_runtime_snapshot()
    romario=universe.player(9)
    assert club_specific_signing_eligibility(3, romario)[0] is True
