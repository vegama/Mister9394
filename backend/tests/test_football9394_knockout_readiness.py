import pytest

from backend.app.football9394 import (
    KnockoutLeg9394,
    KnockoutRoundRules9394,
    UnresolvedHistoricalRulesError,
    audit_competition_readiness,
    default_registry_9394,
    resolve_knockout_tie,
)


def test_two_leg_tie_uses_away_goals_only_when_explicitly_declared():
    first = KnockoutLeg9394("a", "b", 2, 1)
    second = KnockoutLeg9394("b", "a", 1, 0)
    with_away = KnockoutRoundRules9394("Semifinal", legs=2, away_goals=True)
    without_away = KnockoutRoundRules9394("Semifinal", legs=2, away_goals=False)
    resolved = resolve_knockout_tie(first, with_away, second)
    assert resolved.winner_team_id == "b"
    assert resolved.resolved_by == "away_goals"
    pending = resolve_knockout_tie(first, without_away, second)
    assert pending.winner_team_id is None
    assert pending.pending_decider == "extra_time_penalties"


def test_single_leg_draw_can_require_replay_instead_of_modern_penalties():
    rules = KnockoutRoundRules9394("Ronda", legs=1, replay_on_draw=True)
    result = resolve_knockout_tie(KnockoutLeg9394("a", "b", 1, 1), rules)
    assert result.winner_team_id is None
    assert result.pending_decider == "replay"


def test_universe_gate_refuses_to_certify_unknown_mdb_competitions():
    registry = default_registry_9394()
    audit = audit_competition_readiness(["Primera División", "Segunda División", "Recopa"], registry)
    assert audit.ready is False
    assert audit.unresolved == ("Recopa",)
    with pytest.raises(UnresolvedHistoricalRulesError, match="universo 1993-94 incompleto"):
        audit.require_ready()
