from __future__ import annotations

"""Deep source recovery for the supplied Míster 93/94 Access database.

The MDB is a mixed-edition editor database: some structures and records are
excellent historical inputs while others were maintained in much later years.
This module deliberately separates *what the source says* from *what the 1993
runtime is allowed to trust*.  It also recovers four live Jet4 tables that are
referenced by relationships/forms/queries but missing from the normal
MSysObjects table catalogue (Entrenador, Pais, Tactica and MedioComunicacion).

The output is intended to be persisted as a derived JSON catalogue; the Access
file remains an import/audit source and is not required by the game runtime.
"""

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .mdb_jet4 import Jet4MDB, json_safe


SOURCE_CONFIDENCE = {
    "structural": "source_structure_safe",
    "historical_mixed": "mixed_edition_temporal_verification_required",
    "modern_names": "structure_only_names_not_1993_safe",
}

COACH_ENUMS = {
    "game_tendency": {0: "defensive", 1: "normal", 2: "attacking"},
    "rotation_frequency": {0: "low", 1: "normal", 2: "high"},
    "youth_usage": {0: "low", 1: "normal", 2: "high"},
    "discipline_style": {0: "permissive", 1: "balanced", 2: "strict"},
    "player_relationship": {0: "distant", 1: "normal", 2: "close"},
    "player_judgement": {0: "mediocre", 1: "acceptable", 2: "very_good"},
    "set_piece_usage": {0: "low", 1: "normal", 2: "high"},
}

CLUB_SQUAD_BUILDING = {
    0: "signings_first_academy_second",
    1: "academy_first_signings_second",
    2: "mixed",
}

ACADEMY_ORIGIN = {
    0: "region_only",
    1: "region",
    2: "country",
    3: "international",
    4: "very_international",
}

ACADEMY_LEVEL = {
    0: "basic",
    1: "first_team_level",
    2: "prolific",
}

PLAYER_INJURY_PRONENESS = {
    0: "normal",
    1: "injury_prone",
    2: "very_injury_prone",
    3: "chronic",
}

PLAYER_HIDDEN_TRAIT_DESCRIPTIONS = {
    "individualist": "Destaca por realizar jugadas individuales.",
    "killer_pass": "Busca con frecuencia el último pase.",
    "holds_ball": "Destaca por conservar el balón sin avanzar.",
    "long_shots": "Intenta tiros de media o larga distancia.",
    "cuts_inside": "Tiende a ir hacia el centro cuando juega por banda.",
    "first_time_play": "Destaca por tocar de primeras.",
    "dives": "Tiende a tirarse dentro del área.",
}


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clean(*parts: Any) -> str:
    return " ".join(str(part).strip() for part in parts if part and str(part).strip())


def _int_list(value: Any) -> list[int]:
    if not isinstance(value, str):
        return []
    out: list[int] = []
    for token in value.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            out.append(int(token))
        except ValueError:
            continue
    return out


def recover_orphan_source_tables(db: Jet4MDB) -> dict[str, Any]:
    """Find source tables that still exist physically but lost catalogue rows."""
    return {
        "Entrenador": db.find_table_by_columns(
            {"Id", "Apodo", "Tactica_ppal", "TendenciaJuego", "FrecuenciaRotaciones",
             "UsoCantera", "RelacionJugadores", "OjoJugadores", "CALIDAD", "PlantillaCorta"},
            min_rows=1000, name="Entrenador",
        ),
        "Pais": db.find_table_by_columns(
            {"Id", "Nombre", "IdContinente", "Comunitario", "PrestigioLiga", "PtsFIFA"},
            min_rows=100, name="Pais",
        ),
        "Tactica": db.find_table_by_columns(
            {"Nombre", "Posiciones", "Ambitos", "Libertades", "Roles", "Tipo_juego",
             "Distribucion_balon", "Nivel_presion", "Tipo_marcaje", "Manager", "Tipo"},
            excluded_columns={"Predefinida"}, min_rows=10, name="Tactica",
        ),
        "MedioComunicacion": db.find_table_by_columns(
            {"Id", "Tipo", "Nombre", "Nombre_corto", "Pais", "Equipo", "Prestigio",
             "Nivel_seguimiento", "Fanatismo"},
            min_rows=100, name="MedioComunicacion",
        ),
    }


def _manager_rows(db: Jet4MDB, table: Any) -> list[dict[str, Any]]:
    rows = []
    for row in db.rows_from_table(table):
        source_id = _as_int(row.get("Id"))
        if source_id is None:
            continue
        patterns = [
            pattern for key in ("Patron_jug1", "Patron_jug2", "Patron_jug3", "Patron_jug4", "Patron_jug5")
            if (pattern := _as_int(row.get(key))) not in (None, 0)
        ]
        rows.append({
            "source_id": source_id,
            "cpu": bool(row.get("CPU")),
            "display_name": str(row.get("Apodo") or _clean(row.get("Nombre"), row.get("Apellido1"), row.get("Apellido2")) or f"Entrenador {source_id}"),
            "first_name": row.get("Nombre"),
            "surname1": row.get("Apellido1"),
            "surname2": row.get("Apellido2"),
            "nickname": row.get("Mote"),
            "birth_city_id": _as_int(row.get("CiudadNacimiento")),
            "birth_country_id": _as_int(row.get("PaisNacimiento")),
            "birth_date": row.get("FechaNacimiento"),
            # The editor describes Categoria as global public reputation and
            # CALIDAD as the precision with which players follow instructions /
            # ability to achieve objectives.
            "reputation_category": _as_int(row.get("Categoria")),
            "coaching_quality": _as_int(row.get("CALIDAD")),
            "primary_tactic": row.get("Tactica_ppal"),
            "attacking_tactic": row.get("Tactica_variante_ataque"),
            "defensive_tactic": row.get("Tactica_variante_defensa"),
            "game_tendency": COACH_ENUMS["game_tendency"].get(_as_int(row.get("TendenciaJuego"))),
            "rotation_frequency": COACH_ENUMS["rotation_frequency"].get(_as_int(row.get("FrecuenciaRotaciones"))),
            "youth_usage": COACH_ENUMS["youth_usage"].get(_as_int(row.get("UsoCantera"))),
            "preferred_player_pattern_ids": patterns,
            "discipline_style": COACH_ENUMS["discipline_style"].get(_as_int(row.get("Disciplina"))),
            "player_relationship": COACH_ENUMS["player_relationship"].get(_as_int(row.get("RelacionJugadores"))),
            "player_judgement": COACH_ENUMS["player_judgement"].get(_as_int(row.get("OjoJugadores"))),
            "set_piece_usage": COACH_ENUMS["set_piece_usage"].get(_as_int(row.get("UsoJugadasEstrategia"))),
            "prefers_small_squad": bool(row.get("PlantillaCorta")),
            "other_data": row.get("OTROS_DATOS"),
            "contract_years": _as_int(row.get("AnosContrato")),
            "contract_years_served": _as_int(row.get("AnosContratoLleva")),
            "salary": _as_int(row.get("Sueldo")),
            "temporal_confidence": SOURCE_CONFIDENCE["historical_mixed"],
        })
    return rows


def _tactic_rows(db: Jet4MDB, table: Any) -> list[dict[str, Any]]:
    rows = []
    for row in db.rows_from_table(table):
        name = str(row.get("Nombre") or "").strip()
        if not name:
            continue
        rows.append({
            "name": name,
            "positions": _int_list(row.get("Posiciones")),
            "scopes": _int_list(row.get("Ambitos")),
            "freedoms": _int_list(row.get("Libertades")),
            "role_ids": _int_list(row.get("Roles")),
            "game_type": _as_int(row.get("Tipo_juego")),
            "ball_distribution": _as_int(row.get("Distribucion_balon")),
            "pressing_level": _as_int(row.get("Nivel_presion")),
            "marking_type": _as_int(row.get("Tipo_marcaje")),
            "manager_label": row.get("Manager"),
            "formation_type": row.get("Tipo"),
            "source_date": row.get("Fecha"),
            "source_time": row.get("Hora"),
            # Geometry/role arrays are valid structural data. Manager-to-tactic
            # attribution may be from later editor revisions and is not itself
            # proof that a 1993 coach used that exact plan historically.
            "temporal_confidence": SOURCE_CONFIDENCE["historical_mixed"],
        })
    return rows


def _role_rows(db: Jet4MDB) -> list[dict[str, Any]]:
    return [
        {"source_id": int(row["Id"]), "name": str(row.get("Nombre") or "")}
        for row in db.rows("Rol") if isinstance(row.get("Id"), int)
    ]


def _pattern_rows(db: Jet4MDB) -> list[dict[str, Any]]:
    return [
        {
            "source_id": int(row["Id"]),
            "name": str(row.get("Patron") or ""),
            "description": str(row.get("Descripción") or ""),
            "role_id": _as_int(row.get("Rol")),
        }
        for row in db.rows("PatronJugador") if isinstance(row.get("Id"), int)
    ]


def _stadium_rows(db: Jet4MDB) -> list[dict[str, Any]]:
    return [
        {
            "source_id": int(row["Id"]),
            "name": str(row.get("Nombre") or ""),
            "short_name": row.get("NombreCorto"),
            "without_article": bool(row.get("SinPronombre")),
            "width_m": _as_int(row.get("Ancho")),
            "length_m": _as_int(row.get("Largo")),
            "capacity": _as_int(row.get("Aforo")),
            "city_id": _as_int(row.get("Ciudad")),
            "stars": _as_int(row.get("Estrellas")),
            "grass_quality": _as_int(row.get("CalidadCesped")),
            "temporal_confidence": SOURCE_CONFIDENCE["historical_mixed"],
        }
        for row in db.rows("Estadio") if isinstance(row.get("Id"), int)
    ]


def _city_rows(db: Jet4MDB) -> list[dict[str, Any]]:
    return [
        {
            "source_id": int(row["Id"]), "name": str(row.get("Nombre") or ""),
            "country_id": _as_int(row.get("Pais")), "climate_id": _as_int(row.get("Clima")),
            "region_id": _as_int(row.get("RegionGentilicia")),
            "region_id_secondary": _as_int(row.get("RegionGentilicia2")),
            "gentilic": row.get("Gentilicio"), "gentilic_f": row.get("GentilicioF"),
            "gentilic_plural": row.get("GentilicioPlural"),
        }
        for row in db.rows("Ciudad") if isinstance(row.get("Id"), int)
    ]


def _country_rows(db: Jet4MDB, table: Any) -> list[dict[str, Any]]:
    return [
        {
            "source_id": int(row["Id"]), "name": str(row.get("Nombre") or ""),
            "initials": row.get("Siglas"), "continent_id": _as_int(row.get("IdContinente")),
            "gentilic": row.get("Gentilicio"), "gentilic_f": row.get("GentilicioF"),
            "gentilic_plural": row.get("GentilicioPlural"),
            # Community/FIFA/prestige fields are retained for provenance only;
            # the 1993 rules engine remains authoritative for historical status.
            "source_community_flag": bool(row.get("Comunitario")),
            "source_league_prestige": _as_int(row.get("PrestigioLiga")),
            "source_national_team_prestige": _as_int(row.get("PrestigioSeleccion")),
            "uses_second_surname": bool(row.get("Segundo_apellido")),
            "source_world_cup_participant": bool(row.get("Mundialista")),
            "source_confederations_cup_participant": bool(row.get("Copa_confederaciones")),
            "source_sporadic_stars": _as_int(row.get("Cracks_esporadicos")),
            "source_honours": {
                "world_cups": _as_int(row.get("PalmaresMundial")),
                "continental": _as_int(row.get("PalmaresContinental")),
                "confederations": _as_int(row.get("PalmaresConfederaciones")),
            },
            "source_fifa_points": _as_int(row.get("PtsFIFA")),
            "source_national_manager_id": _as_int(row.get("Entrenador")),
            "temporal_confidence": SOURCE_CONFIDENCE["historical_mixed"],
        }
        for row in db.rows_from_table(table) if isinstance(row.get("Id"), int)
    ]


def _referee_rows(db: Jet4MDB) -> list[dict[str, Any]]:
    # Arbitro2 is a source-side backup/variant of Arbitro: all 3,511 ids and
    # every football parameter match, while 1,064 birth dates differ.  Keep
    # both dates as provenance and never use DOB as evidence of 1993 identity.
    backup = {int(row["Id"]): row for row in db.rows("Arbitro2") if isinstance(row.get("Id"), int)}
    out: list[dict[str, Any]] = []
    for row in db.rows("Arbitro"):
        if not isinstance(row.get("Id"), int):
            continue
        source_id = int(row["Id"])
        other = backup.get(source_id) or {}
        birth_date = row.get("FechaNacimiento")
        backup_birth_date = other.get("FechaNacimiento")
        out.append({
            "source_id": source_id,
            "display_name": _clean(row.get("Nombre"), row.get("Apellido1"), row.get("Apellido2")) or f"Árbitro {source_id}",
            "first_name": row.get("Nombre"), "surname1": row.get("Apellido1"), "surname2": row.get("Apellido2"),
            "birth_city_id": _as_int(row.get("CiudadNacimiento")),
            "birth_country_id": _as_int(row.get("PaisNacimiento")),
            "birth_date": birth_date,
            "backup_birth_date": backup_birth_date,
            "birth_date_conflict": bool(birth_date and backup_birth_date and birth_date != backup_birth_date),
            "yellow_tendency": row.get("Amarillas"),
            "red_tendency": row.get("Rojas"),
            "quality": _as_int(row.get("Calidad")),
            "association": row.get("Colegio"), "profession": row.get("Profesion"),
            "league_id": _as_int(row.get("Liga")),
            # A source maintenance query rewrites referee DOBs and the backup
            # confirms widespread DOB divergence. Names also mix editions.
            "temporal_confidence": SOURCE_CONFIDENCE["historical_mixed"],
        })
    return out


def _injury_catalog(db: Jet4MDB) -> dict[str, Any]:
    return {
        "generic": [json_safe(row) for row in db.rows("LesionGenerica")],
        "specific": [json_safe(row) for row in db.rows("LesionEspecifica")],
        "body_zones": [json_safe(row) for row in db.rows("LesionZonaCorporalGenerica")],
        "specific_body_zones": [json_safe(row) for row in db.rows("LesionZonaCorporalEspecifica")],
        "confidence": SOURCE_CONFIDENCE["structural"],
    }


def _name_pools(db: Jet4MDB) -> dict[str, Any]:
    grouped: dict[int, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {"first_names": [], "surnames": []})
    for row in db.rows("_NombresYApellidos"):
        country_id = _as_int(row.get("Pais"))
        text = str(row.get("Txt") or "").strip()
        if country_id is None or not text:
            continue
        item = {
            "text": text,
            "weight": _as_int(row.get("Ponderacion")) or 1,
            "validated": bool(row.get("Validado")),
        }
        grouped[country_id]["surnames" if row.get("Apellido") else "first_names"].append(item)
    return {str(country_id): values for country_id, values in sorted(grouped.items())}


def _region_rows(db: Jet4MDB) -> list[dict[str, Any]]:
    return [
        {
            "source_id": int(row["Id"]),
            "name": str(row.get("Nombre") or ""),
            "country_id": _as_int(row.get("Pais")),
            "gentilic": row.get("Gentilicio"),
            "gentilic_f": row.get("GentilicioF"),
            "gentilic_plural": row.get("GentilicioPlural"),
        }
        for row in db.rows("RegionGentiliciaOpcional") if isinstance(row.get("Id"), int)
    ]


def _continent_rows(db: Jet4MDB) -> list[dict[str, Any]]:
    # Confederation/name topology is useful; source competition names and
    # FechaInicioSelecciones are later-edition state and remain provenance only.
    return [
        {
            "source_id": int(row["Id"]),
            "name": str(row.get("Nombre") or ""),
            "confederation": row.get("Confederacion"),
            "coefficient": _as_int(row.get("Coeficiente")),
            "source_competition_1": row.get("NombreComp1"),
            "source_competition_2": row.get("NombreComp2"),
            "source_national_team_start": row.get("FechaInicioSelecciones"),
            "temporal_confidence": SOURCE_CONFIDENCE["historical_mixed"],
        }
        for row in db.rows("Continente") if isinstance(row.get("Id"), int)
    ]


def build_source_catalog(path: str | Path) -> dict[str, Any]:
    db = Jet4MDB(path)
    orphan = recover_orphan_source_tables(db)
    managers = _manager_rows(db, orphan["Entrenador"])
    tactics = _tactic_rows(db, orphan["Tactica"])
    countries = _country_rows(db, orphan["Pais"])
    media = [
        {
            **json_safe(row),
            "temporal_confidence": SOURCE_CONFIDENCE["modern_names"],
        }
        for row in db.rows_from_table(orphan["MedioComunicacion"])
    ]
    correspondents = [
        {**json_safe(row), "temporal_confidence": SOURCE_CONFIDENCE["modern_names"]}
        for row in db.rows("MedioCorresponsal")
    ]
    climate = [json_safe(row) for row in db.rows("Clima")]
    language_groups = [json_safe(row) for row in db.rows("_GruposIdiomas")]
    country_language_groups = [json_safe(row) for row in db.rows("_RelPaisesGruposIdiomas")]
    return json_safe({
        "schema_version": 1,
        "source_kind": "derived_from_supplied_jet4_mdb",
        "provenance_policy": {
            "source_structure_safe": "La semántica/estructura puede alimentar sistemas del juego.",
            "mixed_edition_temporal_verification_required": "Conservar y usar sólo tras validar si el dato concreto corresponde a 1993-94.",
            "structure_only_names_not_1993_safe": "Usar el modelo de datos; no presentar sus nombres/registros como históricos de 1993.",
        },
        "source_design_semantics": {
            "coach": {
                "quality": "Precisión con la que los jugadores siguen sus órdenes y capacidad de conseguir objetivos.",
                "game_tendency": "Defensivo/normal/ofensivo; el formulario original indica que, combinado con la calidad, influye en el desarrollo de jugadores.",
                "preferred_player_patterns": "Hasta cinco tipos de jugador que el entrenador suele utilizar; normalmente tienen sitio fijo en el once.",
            },
            "player": {
                "injury_proneness": PLAYER_INJURY_PRONENESS,
                "progression_mean": "Escala 0..9 de progresión.",
                "fan_affection": "Escala 0..9 de cariño actual de la afición, variable durante la temporada.",
                "hidden_traits": PLAYER_HIDDEN_TRAIT_DESCRIPTIONS,
            },
            "club": {
                "squad_building": CLUB_SQUAD_BUILDING,
                "academy_origin": ACADEMY_ORIGIN,
                "academy_level": ACADEMY_LEVEL,
                "special_academy_pattern": "Patrón de jugador que suele producir la cantera con mayor frecuencia.",
                "star_sporting_director": "Especialista excepcional en captar jóvenes desconocidos que pueden convertirse en estrellas.",
            },
        },
        "roles": _role_rows(db),
        "player_patterns": _pattern_rows(db),
        "managers": managers,
        "tactics": tactics,
        "referees": _referee_rows(db),
        "stadiums": _stadium_rows(db),
        "cities": _city_rows(db),
        "regions": _region_rows(db),
        "climates": climate,
        "continents": _continent_rows(db),
        "countries": countries,
        "injuries": _injury_catalog(db),
        "name_pools": _name_pools(db),
        "language_groups": language_groups,
        "country_language_groups": country_language_groups,
        "media": media,
        "media_correspondents": correspondents,
        "media_correspondent_links": [json_safe(row) for row in db.rows("MedioRelCorresponsal")],
        "counts": {
            "managers": len(managers), "tactics": len(tactics),
            "referees": db.table("Arbitro").num_rows, "stadiums": db.table("Estadio").num_rows,
            "cities": db.table("Ciudad").num_rows, "regions": db.table("RegionGentiliciaOpcional").num_rows,
            "continents": db.table("Continente").num_rows, "countries": len(countries),
            "roles": db.table("Rol").num_rows, "player_patterns": db.table("PatronJugador").num_rows,
            "generic_injuries": db.table("LesionGenerica").num_rows,
            "specific_injuries": db.table("LesionEspecifica").num_rows,
            "weighted_names": db.table("_NombresYApellidos").num_rows,
            "media": len(media), "media_correspondents": len(correspondents),
        },
    })
