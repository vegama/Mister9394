import pytest
from backend.app.football9394 import CompetitionFormatSpec9394, CompetitionStageRules9394


def test_multistage_format_requires_historical_details_in_each_stage():
    group=CompetitionStageRules9394(
        id="groups",name="Fase de grupos",kind="group",entrants=8,qualifiers=4,
        round_robin_cycles=2,points_win=2,points_draw=1,points_loss=0,
    )
    semi=CompetitionStageRules9394(
        id="semis",name="Semifinal",kind="knockout",entrants=4,qualifiers=2,legs_per_tie=2,
        away_goals=True,replay_on_draw=False,extra_time=True,penalties=True,neutral_venue=False,
    )
    final=CompetitionStageRules9394(
        id="final",name="Final",kind="final",entrants=2,qualifiers=1,legs_per_tie=1,
        away_goals=False,replay_on_draw=False,extra_time=True,penalties=True,neutral_venue=True,
    )
    spec=CompetitionFormatSpec9394("demo","1993-94",(group,semi,final))
    spec.validate()


def test_format_rejects_stage_handoff_that_does_not_match():
    a=CompetitionStageRules9394(id="a",name="A",kind="league",entrants=8,qualifiers=3,round_robin_cycles=1,points_win=2,points_draw=1,points_loss=0)
    b=CompetitionStageRules9394(id="b",name="B",kind="final",entrants=2,qualifiers=1,legs_per_tie=1,away_goals=False,replay_on_draw=False,extra_time=True,penalties=True,neutral_venue=True)
    with pytest.raises(ValueError,match="clasifica 3"):
        CompetitionFormatSpec9394("broken","1993-94",(a,b)).validate()


def test_knockout_stage_has_no_implicit_modern_tiebreak_defaults():
    bad=CompetitionStageRules9394(id="r1",name="R1",kind="knockout",entrants=4,qualifiers=2,legs_per_tie=2)
    with pytest.raises(ValueError,match="away_goals"):
        bad.validate()
