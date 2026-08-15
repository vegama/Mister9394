from __future__ import annotations

"""Certified non-standard 1993 competition structures.

These specs exist separately from simple league rules because several MDB rows
look like ordinary leagues but historically were split-season or multi-stage
competitions.  We model the historical structure rather than trusting those
simplified editor rows.
"""

from .format_graph import CompetitionFormatGraph9394, FormatStageNode9394, FormatTransition9394

APSL_1993_FORMAT = CompetitionFormatGraph9394(
    competition_id="usa_apsl_1993",
    season="1993-94",
    stages=(
        FormatStageNode9394(
            id="regular", name="Temporada regular", kind="league", entrants=7, qualifiers=4,
            round_robin_cycles=4, scoring_system_id="apsl_1993",
            qualification_policy="top_4",
            notes=("Cada pareja se enfrenta cuatro veces: 24 partidos por club.",),
        ),
        FormatStageNode9394(
            id="playoffs", name="Playoffs", kind="knockout", entrants=4, qualifiers=1,
            legs_per_tie=1, rounds=2, away_goals=False, extra_time=True, penalties=True,
            neutral_venue=False, qualification_policy="single_elimination",
        ),
    ),
    transitions=(FormatTransition9394("regular", "playoffs", 4),),
    champion_stage_id="playoffs",
)

JLEAGUE_1993_FORMAT = CompetitionFormatGraph9394(
    competition_id="jpn_jleague_1993",
    season="1993-94",
    stages=(
        FormatStageNode9394(
            id="suntory", name="Suntory Series", kind="league", entrants=10, qualifiers=1,
            round_robin_cycles=2, scoring_system_id="jleague_1993_wins",
            qualification_policy="most_wins",
        ),
        FormatStageNode9394(
            id="nicos", name="NICOS Series", kind="league", entrants=10, qualifiers=1,
            round_robin_cycles=2, scoring_system_id="jleague_1993_wins",
            qualification_policy="most_wins",
        ),
        FormatStageNode9394(
            id="championship", name="Suntory Championship '93", kind="championship",
            entrants=2, qualifiers=1, legs_per_tie=2, away_goals=False, extra_time=True,
            penalties=True, neutral_venue=False,
            notes=("Si un club gana ambas series existe una contingencia especial de acceso a la final.",),
        ),
    ),
    transitions=(
        FormatTransition9394("suntory", "championship", 1),
        FormatTransition9394("nicos", "championship", 1),
    ),
    champion_stage_id="championship",
)

BRAZIL_SERIE_A_1993_FORMAT = CompetitionFormatGraph9394(
    competition_id="bra_serie_a_1993",
    season="1993-94",
    stages=(
        FormatStageNode9394(
            id="groups_ab", name="Primera fase · grupos A/B", kind="group", entrants=16,
            qualifiers=6, group_count=2, round_robin_cycles=2, scoring_system_id="standard_2_1_0",
            qualification_policy="top_3_each_group",
        ),
        FormatStageNode9394(
            id="groups_cd", name="Primera fase · grupos C/D", kind="group", entrants=16,
            qualifiers=4, group_count=2, round_robin_cycles=2, scoring_system_id="standard_2_1_0",
            qualification_policy="top_2_each_group",
            relegation_policy="bottom_4_each_group",
        ),
        FormatStageNode9394(
            id="intermediate", name="Fase intermedia", kind="knockout", entrants=4,
            qualifiers=2, legs_per_tie=2, rounds=1, away_goals=False, extra_time=True,
            penalties=True, neutral_venue=False,
        ),
        FormatStageNode9394(
            id="second_phase", name="Segunda fase", kind="group", entrants=8, qualifiers=2,
            group_count=2, round_robin_cycles=2, scoring_system_id="standard_2_1_0",
            qualification_policy="group_winners",
        ),
        FormatStageNode9394(
            id="final", name="Final", kind="final", entrants=2, qualifiers=1,
            legs_per_tie=2, rounds=1, away_goals=False, extra_time=False, penalties=False,
            neutral_venue=False, qualification_policy="better_campaign_has_draw_advantage",
        ),
    ),
    transitions=(
        FormatTransition9394("groups_ab", "second_phase", 6),
        FormatTransition9394("groups_cd", "intermediate", 4),
        FormatTransition9394("intermediate", "second_phase", 2),
        FormatTransition9394("second_phase", "final", 2),
    ),
    champion_stage_id="final",
    notes=("La MDB simplifica esta competición a 20 clubes; el formato histórico real tuvo 32.",),
)

MEXICO_1993_94_FORMAT = CompetitionFormatGraph9394(
    competition_id="mex_primera_1993_94",
    season="1993-94",
    stages=(
        FormatStageNode9394(
            id="regular", name="Fase regular", kind="league", entrants=20, qualifiers=8,
            group_count=4, round_robin_cycles=2, scoring_system_id="standard_2_1_0",
            qualification_policy="group_top2_with_reclassification",
            relegation_policy="lowest_relegation_coefficient",
            notes=("Los 20 clubes juegan todos contra todos pese a estar repartidos en cuatro grupos de clasificación.",),
        ),
        FormatStageNode9394(
            id="liguilla", name="Liguilla", kind="knockout", entrants=8, qualifiers=1,
            legs_per_tie=2, rounds=3, away_goals=True, extra_time=True, penalties=True,
            neutral_venue=False,
        ),
    ),
    transitions=(FormatTransition9394("regular", "liguilla", 8),),
    champion_stage_id="liguilla",
)


COLOMBIA_1993_FORMAT = CompetitionFormatGraph9394(
    competition_id="col_primera_a_1993",
    season="1993-94",
    stages=(
        FormatStageNode9394(
            id="apertura", name="Copa Mustang I", kind="group", entrants=16, qualifiers=4,
            group_count=2, round_robin_cycles=2, scoring_system_id="standard_2_1_0",
            qualification_policy="top2_each_group_to_bonus_allocation",
        ),
        FormatStageNode9394(
            id="bonus_apertura", name="Definición de bonificación Apertura", kind="knockout",
            entrants=4, qualifiers=4, legs_per_tie=2, rounds=1, away_goals=False,
            extra_time=True, penalties=True, neutral_venue=False,
            qualification_policy="rank_winners_and_runners_up_for_bonus",
        ),
        FormatStageNode9394(
            id="finalizacion", name="Copa Mustang II", kind="league", entrants=16, qualifiers=8,
            round_robin_cycles=2, scoring_system_id="standard_2_1_0",
            qualification_policy="aggregate_apertura_finalizacion_top8",
            relegation_policy="aggregate_bottom1",
        ),
        FormatStageNode9394(
            id="semifinals", name="Cuadrangulares semifinales", kind="group", entrants=8, qualifiers=4,
            group_count=2, round_robin_cycles=2, scoring_system_id="standard_2_1_0_plus_season_bonus",
            qualification_policy="top2_each_group",
        ),
        FormatStageNode9394(
            id="final", name="Cuadrangular final", kind="group", entrants=4, qualifiers=1,
            group_count=1, round_robin_cycles=2, scoring_system_id="standard_2_1_0_bonus_as_tiebreak",
            qualification_policy="group_winner",
        ),
    ),
    transitions=(
        FormatTransition9394("apertura", "bonus_apertura", 4),
        FormatTransition9394("finalizacion", "semifinals", 8),
        FormatTransition9394("semifinals", "final", 4),
    ),
    champion_stage_id="final",
    notes=("La reclasificación suma 44 partidos de Apertura + Finalización; los partidos de definición de bonificación no se añaden a esa tabla.",),
)

for _format in (APSL_1993_FORMAT, JLEAGUE_1993_FORMAT, BRAZIL_SERIE_A_1993_FORMAT, MEXICO_1993_94_FORMAT, COLOMBIA_1993_FORMAT):
    _format.validate()

CERTIFIED_COMPLEX_FORMATS_9394 = {
    spec.competition_id: spec for spec in (
        APSL_1993_FORMAT, JLEAGUE_1993_FORMAT, BRAZIL_SERIE_A_1993_FORMAT, MEXICO_1993_94_FORMAT, COLOMBIA_1993_FORMAT
    )
}
