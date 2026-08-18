from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


DecisiveTieContext = Literal["champion", "europe", "promotion", "relegation"]


TieBreaker = Literal[
    "head_to_head_points",
    "head_to_head_goal_difference",
    "overall_wins",
    "overall_goal_difference",
    "overall_goals_scored",
    "overall_away_goals_scored",
    "overall_goals_against",
    "overall_away_goals_against",
    "playoff",
]


@dataclass(frozen=True, slots=True)
class CompetitionRules9394:
    """Competition-specific historical rules for one 1993-94 competition.

    No implicit modern defaults are allowed: the importer must either attach a
    resolved ruleset to a competition or mark it unresolved for audit.
    """

    id: str
    name: str
    country: str
    season: str = "1993-94"
    competition_type: Literal["league", "cup", "continental", "supercup"] = "league"
    points_win: int | None = None
    points_draw: int | None = None
    points_loss: int | None = None
    teams: int | None = None
    rounds: int | None = None
    tie_breakers: tuple[TieBreaker, ...] = ()
    direct_relegation_places: tuple[int, ...] = ()
    relegation_playoff_places: tuple[int, ...] = ()
    direct_promotion_places: tuple[int, ...] = ()
    promotion_playoff_places: tuple[int, ...] = ()
    decisive_playoff_contexts: tuple[DecisiveTieContext, ...] = ()
    reserve_teams_allowed: bool = True
    reserve_may_share_division_with_parent: bool = False
    reserve_forced_relegation_uses_relegation_slot: bool = True
    notes: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if self.competition_type == "league":
            if self.points_win is None or self.points_draw is None or self.points_loss is None:
                raise ValueError(f"{self.id}: una liga 1993-94 necesita puntuación explícita")
            if not self.tie_breakers:
                raise ValueError(f"{self.id}: una liga 1993-94 necesita desempates explícitos")
        if self.season != "1993-94":
            raise ValueError(f"{self.id}: este registro no pertenece a 1993-94")


SPAIN_PRIMERA_1993_94 = CompetitionRules9394(
    id="esp_primera_1993_94",
    name="Primera División",
    country="España",
    points_win=2,
    points_draw=1,
    points_loss=0,
    teams=20,
    rounds=38,
    tie_breakers=(
        "head_to_head_points",
        "head_to_head_goal_difference",
        "overall_goal_difference",
        "overall_goals_scored",
        "playoff",
    ),
    direct_relegation_places=(19, 20),
    relegation_playoff_places=(17, 18),
    reserve_teams_allowed=True,
    reserve_may_share_division_with_parent=False,
    reserve_forced_relegation_uses_relegation_slot=True,
    notes=(
        "Los puestos 17 y 18 disputan promoción de permanencia/ascenso contra Segunda.",
        "Un filial nunca puede coincidir en categoría con su primer equipo.",
    ),
)

SPAIN_SEGUNDA_1993_94 = CompetitionRules9394(
    id="esp_segunda_1993_94",
    name="Segunda División",
    country="España",
    points_win=2,
    points_draw=1,
    points_loss=0,
    teams=20,
    rounds=38,
    tie_breakers=(
        "head_to_head_points",
        "head_to_head_goal_difference",
        "overall_goal_difference",
        "overall_goals_scored",
        "playoff",
    ),
    direct_promotion_places=(1, 2),
    promotion_playoff_places=(3, 4),
    direct_relegation_places=(17, 18, 19, 20),
    reserve_teams_allowed=True,
    reserve_may_share_division_with_parent=False,
    reserve_forced_relegation_uses_relegation_slot=True,
    notes=(
        "Los filiales no son elegibles para ascender a una categoría ocupada por su primer equipo.",
        "Si el primer equipo cae a esta división, el filial desciende y ocupa una plaza de descenso.",
    ),
)


def _spain_segunda_b_group_rules(rules_id: str, name: str) -> CompetitionRules9394:
    return CompetitionRules9394(
        id=rules_id, name=name, country="España",
        points_win=2, points_draw=1, points_loss=0,
        teams=20, rounds=38,
        tie_breakers=(
            "head_to_head_points", "head_to_head_goal_difference",
            "overall_goal_difference", "overall_goals_scored", "playoff",
        ),
        direct_relegation_places=(17, 18, 19, 20),
        relegation_playoff_places=(16,),
        promotion_playoff_places=(1, 2, 3, 4),
        reserve_teams_allowed=True,
        reserve_may_share_division_with_parent=False,
        reserve_forced_relegation_uses_relegation_slot=True,
        notes=(
            "Los cuatro primeros acceden a cuatro liguillas de ascenso; cada liguilla contiene un 1.º, 2.º, 3.º y 4.º de grupos de origen distintos.",
            "Los puestos 17.º-20.º descienden a Tercera; los cuatro 16.º disputan una promoción de permanencia a partido único y campo neutral.",
            "Un descenso forzoso de filial por descenso de su primer equipo ocupa una de las plazas de descenso del grupo.",
        ),
    )

SPAIN_SEGUNDA_B_G1_1993_94 = _spain_segunda_b_group_rules("esp_segunda_b_g1_1993_94", "Segunda División B G I")
SPAIN_SEGUNDA_B_G2_1993_94 = _spain_segunda_b_group_rules("esp_segunda_b_g2_1993_94", "Segunda División B G II")
SPAIN_SEGUNDA_B_G3_1993_94 = _spain_segunda_b_group_rules("esp_segunda_b_g3_1993_94", "Segunda División B G III")
SPAIN_SEGUNDA_B_G4_1993_94 = _spain_segunda_b_group_rules("esp_segunda_b_g4_1993_94", "Segunda División B G IV")


FRANCE_DIVISION_1_1993_94 = CompetitionRules9394(
    id="fra_division_1_1993_94",
    name="Division 1",
    country="Francia",
    points_win=2, points_draw=1, points_loss=0,
    teams=20, rounds=38,
    tie_breakers=("overall_goal_difference", "overall_goals_scored"),
    direct_relegation_places=(18, 19, 20),
    notes=(
        "Última temporada francesa con dos puntos por victoria.",
        "Clasificación: puntos, diferencia de goles y goles marcados.",
        "El descenso administrativo real de Marseille no se fuerza en una partida alternativa; las sanciones extraordinarias pertenecen al sistema disciplinario/eventos.",
    ),
)

PORTUGAL_PRIMEIRA_1993_94 = CompetitionRules9394(
    id="por_primeira_1993_94",
    name="Primeira Liga",
    country="Portugal",
    points_win=2, points_draw=1, points_loss=0,
    teams=18, rounds=34,
    tie_breakers=("overall_goal_difference", "overall_goals_scored"),
    direct_relegation_places=(16, 17, 18),
    notes=(
        "Dieciocho clubes y 34 jornadas.",
        "Dos puntos por victoria; los tres últimos descienden a Liga de Honra.",
        "La reconstrucción histórica de clasificación usa diferencia de goles como primer desempate; no se añade ningún criterio moderno oculto si persiste la igualdad.",
    ),
)


SPAIN_SEGUNDA_B_1993_94 = CompetitionRules9394(
    id="esp_segunda_b_1993_94",
    name="Segunda División B",
    country="España",
    points_win=2, points_draw=1, points_loss=0,
    teams=20, rounds=38,
    tie_breakers=(
        "head_to_head_points", "head_to_head_goal_difference",
        "overall_goal_difference", "overall_goals_scored", "playoff",
    ),
    direct_relegation_places=(17, 18, 19, 20),
    relegation_playoff_places=(16,),
    notes=(
        "Cuatro grupos de veinte clubes; los cuatro primeros acceden a la liguilla de ascenso.",
        "Los cuatro últimos de cada grupo bajan y los cuatro 16.º disputan la permanencia.",
    ),
)

SPAIN_SEGUNDA_B_PROMOTION_GROUP_1993_94 = CompetitionRules9394(
    id="esp_segunda_b_promotion_group_1993_94",
    name="Promoción de ascenso a Segunda",
    country="España",
    points_win=2, points_draw=1, points_loss=0,
    teams=4, rounds=6,
    tie_breakers=(
        "head_to_head_points", "head_to_head_goal_difference",
        "overall_goal_difference", "overall_goals_scored", "playoff",
    ),
    direct_promotion_places=(1,),
    notes=("Cuatro liguillas de cuatro; sólo el campeón de cada una asciende a Segunda División.",),
)


URUGUAY_PRIMERA_1993 = CompetitionRules9394(
    id="uru_primera_1993",
    name="Primera División",
    country="Uruguay",
    points_win=2, points_draw=1, points_loss=0,
    teams=13, rounds=24,
    tie_breakers=("overall_goal_difference", "overall_goals_scored", "playoff"),
    decisive_playoff_contexts=("champion",),
    notes=(
        "Trece clubes, todos contra todos a ida y vuelta: 24 partidos por club.",
        "La tabla de 1993 otorgaba dos puntos por victoria.",
        "El movimiento de categoría dependía además de la tabla de descenso y de un repechaje con Segunda; como la MDB no incluye la Segunda uruguaya, esa transición queda desacoplada en vez de inventarse.",
    ),
)


NETHERLANDS_EREDIVISIE_1993_94 = CompetitionRules9394(
    id="ned_eredivisie_1993_94",
    name="Eredivisie",
    country="Países Bajos",
    points_win=2, points_draw=1, points_loss=0,
    teams=18, rounds=34,
    tie_breakers=("overall_goal_difference", "overall_goals_scored"),
    direct_relegation_places=(18,),
    relegation_playoff_places=(16, 17),
    notes=(
        "El último desciende directamente.",
        "16.º y 17.º entran en la nacompetitie con seis clubes de Eerste Divisie.",
    ),
)

NETHERLANDS_EERSTE_1993_94 = CompetitionRules9394(
    id="ned_eerste_1993_94",
    name="Eerste Divisie",
    country="Países Bajos",
    points_win=2, points_draw=1, points_loss=0,
    teams=18, rounds=34,
    tie_breakers=("overall_goal_difference", "overall_goals_scored"),
    direct_promotion_places=(1,),
    notes=(
        "El campeón asciende directamente.",
        "Cuatro ganadores de periodo y los dos mejores clubes elegibles restantes acceden a la nacompetitie.",
    ),
)

NETHERLANDS_NACOMPETITIE_GROUP_1993_94 = CompetitionRules9394(
    id="ned_nacompetitie_group_1993_94",
    name="Nacompetitie",
    country="Países Bajos",
    points_win=2, points_draw=1, points_loss=0,
    teams=4, rounds=6,
    tie_breakers=("overall_goal_difference", "overall_goals_scored", "playoff"),
    direct_promotion_places=(1,),
    decisive_playoff_contexts=("promotion",),
    notes=("Dos grupos de cuatro a ida y vuelta; el ganador de cada grupo obtiene plaza de Eredivisie.",),
)


ARGENTINA_PRIMERA_1993_94 = CompetitionRules9394(
    id="arg_primera_1993_94",
    name="Campeonato de Primera División",
    country="Argentina",
    points_win=2, points_draw=1, points_loss=0,
    teams=20, rounds=38,
    tie_breakers=("playoff",),
    decisive_playoff_contexts=("champion",),
    notes=(
        "La temporada contiene Apertura y Clausura independientes, 19 fechas cada uno y dos campeones.",
        "El Clausura invierte las localías del Apertura.",
        "Los dos descensos se determinan por promedio de puntos/partidos de los últimos tres ciclos.",
    ),
)

ARGENTINA_SHORT_TOURNAMENT_1993_94 = CompetitionRules9394(
    id="arg_short_tournament_1993_94",
    name="Apertura/Clausura",
    country="Argentina",
    points_win=2, points_draw=1, points_loss=0,
    teams=20, rounds=19,
    tie_breakers=("playoff",),
    decisive_playoff_contexts=("champion",),
    notes=("Todos contra todos a una sola rueda; empate en el primer puesto requiere desempate explícito.",),
)


MEXICO_PRIMERA_1993_94 = CompetitionRules9394(
    id="mex_primera_1993_94",
    name="Primera División",
    country="México",
    points_win=2, points_draw=1, points_loss=0,
    teams=20, rounds=38,
    tie_breakers=("overall_goal_difference", "overall_goals_scored", "playoff"),
    notes=(
        "Los veinte clubes juegan todos contra todos a visita recíproca y se encuadran además en cuatro grupos de cinco para clasificar a la liguilla.",
        "Los dos primeros de cada grupo ocupan las ocho plazas nominales; uno o dos clubes de fuera del top-2 de su grupo pueden forzar reclasificación si superan en puntos a sublíderes de otros grupos.",
        "Reclasificación y liguilla se disputan a ida y vuelta con gol de visitante; igualdad posterior se resuelve con prórroga y penaltis.",
        "El descenso se determina por el menor cociente de puntos por partido de las tres temporadas computables, no por la posición de la tabla general.",
    ),
)


COLOMBIA_PRIMERA_A_1993 = CompetitionRules9394(
    id="col_primera_a_1993",
    name="Primera A",
    country="Colombia",
    points_win=2, points_draw=1, points_loss=0,
    teams=16, rounds=44,
    tie_breakers=(
        "overall_wins", "overall_goal_difference", "overall_goals_scored",
        "overall_away_goals_scored", "overall_goals_against", "overall_away_goals_against",
    ),
    direct_relegation_places=(16,),
    notes=(
        "Apertura: dos grupos de ocho a ida y vuelta (14 partidos por club).",
        "Finalización: todos contra todos a ida y vuelta (30 partidos por club).",
        "La reclasificación suma Apertura + Finalización (44 partidos); los ocho primeros avanzan y el último desciende.",
        "Apertura y Finalización otorgan bonificaciones 1.00/0.75/0.50/0.25 para las fases finales.",
        "En semifinales la bonificación se suma a los puntos; en el cuadrangular final actúa como primer desempate tras los puntos.",
    ),
)

COLOMBIA_APERTURA_GROUP_1993 = CompetitionRules9394(
    id="col_apertura_group_1993", name="Copa Mustang I · Grupo", country="Colombia",
    points_win=2, points_draw=1, points_loss=0, teams=8, rounds=14,
    tie_breakers=COLOMBIA_PRIMERA_A_1993.tie_breakers,
)

COLOMBIA_FINALIZACION_1993 = CompetitionRules9394(
    id="col_finalizacion_1993", name="Copa Mustang II", country="Colombia",
    points_win=2, points_draw=1, points_loss=0, teams=16, rounds=30,
    tie_breakers=COLOMBIA_PRIMERA_A_1993.tie_breakers,
)

COLOMBIA_QUADRANGULAR_1993 = CompetitionRules9394(
    id="col_quadrangular_1993", name="Cuadrangular", country="Colombia",
    points_win=2, points_draw=1, points_loss=0, teams=4, rounds=6,
    tie_breakers=COLOMBIA_PRIMERA_A_1993.tie_breakers,
)


ITALY_SERIE_A_1993_94 = CompetitionRules9394(
    id="ita_serie_a_1993_94",
    name="Serie A",
    country="Italia",
    points_win=2, points_draw=1, points_loss=0,
    teams=18, rounds=34,
    tie_breakers=(
        "head_to_head_points", "head_to_head_goal_difference",
        "overall_goal_difference", "overall_goals_scored",
    ),
    direct_relegation_places=(15, 16, 17, 18),
    decisive_playoff_contexts=("champion", "europe", "relegation"),
    notes=(
        "La classifica avulsa ordena los empates ordinarios.",
        "Los empates decisivos por título, permanencia/descenso o acceso UEFA requieren spareggio.",
    ),
)

ITALY_SERIE_B_1993_94 = CompetitionRules9394(
    id="ita_serie_b_1993_94",
    name="Serie B",
    country="Italia",
    points_win=2, points_draw=1, points_loss=0,
    teams=20, rounds=38,
    tie_breakers=(
        "head_to_head_points", "head_to_head_goal_difference",
        "overall_goal_difference", "overall_goals_scored",
    ),
    direct_promotion_places=(1, 2, 3, 4),
    direct_relegation_places=(17, 18, 19, 20),
    decisive_playoff_contexts=("promotion", "relegation"),
    notes=(
        "Si un empate de puntos cruza la zona de ascenso o descenso, la classifica avulsa selecciona los dos clubes del spareggio neutral.",
    ),
)


ENGLAND_PREMIER_1993_94 = CompetitionRules9394(
    id="eng_premier_1993_94",
    name="Premier League",
    country="Inglaterra",
    points_win=2,
    points_draw=1,
    points_loss=0,
    teams=22,
    rounds=42,
    tie_breakers=(
        "overall_goal_difference",
        "overall_goals_scored",
        "playoff",
    ),
    direct_relegation_places=(20, 21, 22),
    notes=(
        "Veintidós clubes y 42 partidos por equipo en 1993-94.",
        "Míster 93/94 aplica su regla de puntuación congelada de dos puntos por victoria y uno por empate.",
        "Los tres últimos descienden de forma directa.",
    ),
)

GERMANY_BUNDESLIGA_1993_94 = CompetitionRules9394(
    id="ger_bundesliga_1993_94",
    name="1.Bundesliga",
    country="Alemania",
    points_win=2,
    points_draw=1,
    points_loss=0,
    teams=18,
    rounds=34,
    tie_breakers=(
        "overall_goal_difference",
        "overall_goals_scored",
        "head_to_head_points",
        "head_to_head_goal_difference",
        "playoff",
    ),
    direct_relegation_places=(16, 17, 18),
    notes=(
        "La promoción permanencia no estuvo en uso en 1993-94.",
        "Los tres últimos descienden de forma directa.",
    ),
)

SCOTLAND_PREMIER_1993_94 = CompetitionRules9394(
    id="sco_premier_1993_94",
    name="Scottish Premier Division",
    country="Escocia",
    points_win=2,
    points_draw=1,
    points_loss=0,
    teams=12,
    rounds=44,
    tie_breakers=(
        "overall_goal_difference",
        "overall_goals_scored",
        "playoff",
    ),
    direct_relegation_places=(10, 11, 12),
    notes=(
        "Cada pareja se enfrenta cuatro veces: 44 partidos por club.",
        "Tres clubes descienden por la reestructuración a una Premier Division de diez equipos en 1994-95.",
        "La fila MDB declara tres vueltas; el runtime corrige ese dato al formato histórico de cuatro enfrentamientos.",
        "1993-94 fue la última temporada escocesa con dos puntos por victoria.",
    ),
)


for _rules in (
    SPAIN_PRIMERA_1993_94, SPAIN_SEGUNDA_1993_94,
    SPAIN_SEGUNDA_B_G1_1993_94, SPAIN_SEGUNDA_B_G2_1993_94, SPAIN_SEGUNDA_B_G3_1993_94, SPAIN_SEGUNDA_B_G4_1993_94,
    ENGLAND_PREMIER_1993_94, GERMANY_BUNDESLIGA_1993_94, SCOTLAND_PREMIER_1993_94,
    FRANCE_DIVISION_1_1993_94, PORTUGAL_PRIMEIRA_1993_94,
    SPAIN_SEGUNDA_B_1993_94, SPAIN_SEGUNDA_B_PROMOTION_GROUP_1993_94,
    NETHERLANDS_EREDIVISIE_1993_94, NETHERLANDS_EERSTE_1993_94, NETHERLANDS_NACOMPETITIE_GROUP_1993_94,
    ARGENTINA_PRIMERA_1993_94, ARGENTINA_SHORT_TOURNAMENT_1993_94, MEXICO_PRIMERA_1993_94,
    ITALY_SERIE_A_1993_94, ITALY_SERIE_B_1993_94,
):
    _rules.validate()

BELGIUM_FIRST_DIVISION_1993_94 = CompetitionRules9394(
    id="bel_first_division_1993_94",
    name="Eerste Klasse / Division 1",
    country="Bélgica",
    points_win=2, points_draw=1, points_loss=0,
    teams=18, rounds=34,
    tie_breakers=("overall_wins", "overall_goal_difference", "overall_goals_scored"),
    direct_relegation_places=(17, 18),
    notes=(
        "Dieciocho clubes y 34 jornadas; dos puntos por victoria.",
        "Waregem y Genk ocuparon las dos plazas de descenso en 1993-94.",
        "La clasificación histórica conservada prioriza victorias y diferencia de goles para separar empates de puntos.",
    ),
)

TURKEY_FIRST_DIVISION_1993_94 = CompetitionRules9394(
    id="tur_first_division_1993_94",
    name="1. Lig",
    country="Turquía",
    points_win=2, points_draw=1, points_loss=0,
    teams=16, rounds=30,
    tie_breakers=("overall_goal_difference", "overall_goals_scored"),
    direct_relegation_places=(14, 15, 16),
    notes=(
        "Dieciséis clubes y 30 jornadas.",
        "Míster 93/94 aplica su regla de puntuación congelada de dos puntos por victoria y uno por empate.",
        "Los tres últimos descendían de la máxima categoría.",
    ),
)

RUSSIA_SUPREME_LEAGUE_1993 = CompetitionRules9394(
    id="rus_supreme_league_1993",
    name="Supreme League 1993",
    country="Rusia",
    points_win=2, points_draw=1, points_loss=0,
    teams=18, rounds=34,
    tie_breakers=(
        "head_to_head_points", "head_to_head_goal_difference",
        "overall_wins", "overall_goal_difference", "overall_goals_scored",
    ),
    direct_relegation_places=(15, 16, 17, 18),
    notes=(
        "Temporada rusa disputada por año natural en 1993; el motor la integra en el mundo congelado 1993-94 sin renombrarla como una liga 1993-94.",
        "Dieciocho clubes, 34 jornadas y dos puntos por victoria.",
        "Vladivostok, Okean Nakhodka, RostSelMash y Asmaral ocuparon las cuatro plazas de descenso.",
    ),
)

GREECE_ALPHA_ETHNIKI_1993_94 = CompetitionRules9394(
    id="gre_alpha_ethniki_1993_94",
    name="Alpha Ethniki",
    country="Grecia",
    points_win=2, points_draw=1, points_loss=0,
    teams=18, rounds=34,
    tie_breakers=("overall_wins", "overall_goals_scored", "overall_goal_difference"),
    direct_relegation_places=(16, 17, 18),
    notes=(
        "Dieciocho clubes y 34 jornadas; Míster 93/94 aplica dos puntos por victoria y uno por empate.",
        "Panachaiki, Apollon Kalamarias y Naousa ocuparon las tres plazas de descenso en 1993-94.",
        "El orden de los empates de la tabla histórica es compatible con priorizar victorias y después goles marcados antes de la diferencia general; se conserva como criterio histórico de reconstrucción.",
    ),
)
