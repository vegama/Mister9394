from __future__ import annotations

"""Human club structure and responsibility delegation for Míster 93/94.

The historical snapshot contains rich club context but not a complete staff list
for every playable club.  This module therefore keeps a strict provenance
boundary: source-backed hints (for example the sporting-director level) are used
when present, while missing employees are deterministic *career-generated*
people.  Generated staff are never presented as historical facts.

NF0 is intentionally an infrastructure layer.  Later phases consume the same
responsibility assignments for scouting, training, medical information and
market negotiation instead of creating parallel ownership settings.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from random import Random
from typing import Any


STAFF_SCHEMA_9394 = 1


@dataclass(frozen=True, slots=True)
class StaffRoleSpec:
    key: str
    label: str
    short_label: str
    primary_skill: str


STAFF_ROLES: dict[str, StaffRoleSpec] = {
    "assistant_manager": StaffRoleSpec("assistant_manager", "Segundo entrenador", "2.º entrenador", "tactical"),
    "first_team_coach": StaffRoleSpec("first_team_coach", "Entrenador de primer equipo", "Entrenador", "coaching"),
    "goalkeeping_coach": StaffRoleSpec("goalkeeping_coach", "Entrenador de porteros", "Porteros", "goalkeeping"),
    "physio": StaffRoleSpec("physio", "Fisioterapeuta", "Fisio", "physiotherapy"),
    "scout": StaffRoleSpec("scout", "Ojeador", "Ojeador", "judging_player"),
    "chief_scout": StaffRoleSpec("chief_scout", "Jefe de ojeadores", "Jefe ojeadores", "market_knowledge"),
    "sporting_director": StaffRoleSpec("sporting_director", "Secretario técnico", "Secretario técnico", "negotiation"),
}


SKILL_LABELS = {
    "coaching": "Entrenamiento",
    "tactical": "Táctica",
    "discipline": "Disciplina",
    "judging_player": "Juzgar capacidad",
    "judging_potential": "Juzgar potencial",
    "market_knowledge": "Conocimiento de mercado",
    "negotiation": "Negociación",
    "physiotherapy": "Fisioterapia",
    "youth": "Trabajo con jóvenes",
    "goalkeeping": "Porteros",
}


RESPONSIBILITIES: dict[str, dict[str, Any]] = {
    "lineup_tactics": {
        "label": "Once y táctica",
        "area": "Primer equipo",
        "description": "Decide el once, la convocatoria y el plan táctico del equipo.",
        "skill": "tactical",
        "roles": ("assistant_manager",),
        "default": "manager",
        "workspace": "squad",
        "effect": "Afecta a la selección del once, la convocatoria y la coherencia del plan de partido.",
    },
    "first_team_training": {
        "label": "Entrenamiento del primer equipo",
        "area": "Primer equipo",
        "description": "Organiza el trabajo cotidiano y la carga del primer equipo.",
        "skill": "coaching",
        "roles": ("assistant_manager", "first_team_coach"),
        "default": "assistant_manager",
        "workspace": "training",
        "effect": "Afecta a la calidad útil de las sesiones, la carga acumulada y el desarrollo cotidiano.",
    },
    "match_preparation": {
        "label": "Preparación del próximo partido",
        "area": "Primer equipo",
        "description": "Coordina la preparación específica antes de cada encuentro.",
        "skill": "tactical",
        "roles": ("assistant_manager", "first_team_coach"),
        "default": "assistant_manager",
        "workspace": "training",
        "effect": "Afecta a la preparación específica del rival y a cuánto se aprovecha el trabajo previo al partido.",
    },
    "opposition_reports": {
        "label": "Informes del rival",
        "area": "Scouting",
        "description": "Observa tendencias y amenazas del siguiente adversario.",
        "skill": "judging_player",
        "roles": ("chief_scout", "scout", "assistant_manager"),
        "default": "chief_scout",
        "workspace": "tactics",
        "effect": "Afecta a la fiabilidad y detalle con los que llegan amenazas, tendencias y bajas del rival.",
    },
    "recruitment_search": {
        "label": "Búsqueda de fichajes",
        "area": "Scouting",
        "description": "Dirige encargos y seguimiento de objetivos externos.",
        "skill": "market_knowledge",
        "roles": ("chief_scout", "scout", "sporting_director"),
        "default": "chief_scout",
        "workspace": "market",
        "effect": "Afecta a capacidad, plazo, frescura y precisión de los dossiers de jugadores externos.",
    },
    "transfer_negotiation": {
        "label": "Negociación de traspasos",
        "area": "Mercado",
        "description": "Lleva el contacto y la negociación económica con otros clubes.",
        "skill": "negotiation",
        "roles": ("sporting_director",),
        "default": "sporting_director",
        "workspace": "market",
        "effect": "Afecta a la lectura de precios, los tiempos de respuesta y la fuerza negociadora del club.",
    },
    "contract_renewal": {
        "label": "Renovaciones de contrato",
        "area": "Mercado",
        "description": "Conduce las conversaciones contractuales con la plantilla.",
        "skill": "negotiation",
        "roles": ("sporting_director", "assistant_manager"),
        "default": "sporting_director",
        "workspace": "squad",
        "effect": "Afecta a la calidad de las conversaciones de renovación y al coste de retener la plantilla.",
    },
    "medical_assessment": {
        "label": "Valoración médica",
        "area": "Salud",
        "description": "Centraliza diagnósticos, evolución y recomendaciones de disponibilidad.",
        "skill": "physiotherapy",
        "roles": ("physio",),
        "default": "physio",
        "workspace": "training",
        "effect": "Afecta a la confianza de diagnósticos, riesgo, recuperación y recomendaciones de disponibilidad.",
    },
    "youth_development": {
        "label": "Seguimiento de jóvenes",
        "area": "Desarrollo",
        "description": "Supervisa progresión, adaptación y necesidades de los jugadores jóvenes.",
        "skill": "youth",
        "roles": ("first_team_coach", "assistant_manager", "sporting_director"),
        "default": "first_team_coach",
        "workspace": "squad",
        "effect": "Afecta a la lectura de progresión, adaptación y necesidades futuras de los jóvenes.",
    },
}


# Small deterministic name pools. They are career-generation vocabulary, not a
# claim about historical employees.  The exact generated identity persists in
# the save once created.
_NAME_POOLS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "spain": (("Antonio", "José", "Manuel", "Francisco", "Miguel", "Rafael", "Luis", "Javier"), ("García", "Fernández", "Martínez", "Sánchez", "Romero", "Navarro", "Iglesias", "Méndez")),
    "italy": (("Gianni", "Paolo", "Marco", "Roberto", "Stefano", "Luigi", "Carlo", "Massimo"), ("Rossi", "Bianchi", "Conti", "Ferrari", "Romano", "Moretti", "Galli", "De Luca")),
    "england": (("John", "Peter", "David", "Steve", "Paul", "Alan", "Martin", "Brian"), ("Smith", "Taylor", "Wilson", "Brown", "Walker", "Clarke", "Hughes", "Bennett")),
    "scotland": (("Ian", "Alistair", "Gordon", "Duncan", "Colin", "Graeme", "Neil", "Douglas"), ("Campbell", "Stewart", "Murray", "Fraser", "McLean", "Robertson", "Grant", "Douglas")),
    "russia": (("Aleksandr", "Sergei", "Viktor", "Oleg", "Andrei", "Yuri", "Vladimir", "Nikolai"), ("Ivanov", "Petrov", "Sokolov", "Volkov", "Kuznetsov", "Orlov", "Morozov", "Lebedev")),
    "belgium": (("Marc", "Luc", "Philippe", "Patrick", "Jean", "Dirk", "Michel", "Geert"), ("Peeters", "Janssens", "Maes", "Jacobs", "Willems", "Lambert", "Dubois", "De Smet")),
    "turkey": (("Mehmet", "Mustafa", "Ahmet", "Ali", "Hakan", "Kemal", "Orhan", "Yilmaz"), ("Yilmaz", "Kaya", "Demir", "Sahin", "Celik", "Aydin", "Arslan", "Koc")),
    "greece": (("Giorgos", "Nikos", "Dimitris", "Kostas", "Panagiotis", "Vasilis", "Stavros", "Thanasis"), ("Papadopoulos", "Nikolaidis", "Georgiou", "Dimitriou", "Konstantinou", "Vlachos", "Pappas", "Karagiannis")),
    "netherlands": (("Jan", "Peter", "Johan", "Wim", "Marco", "Ron", "Hans", "Erik"), ("de Jong", "Jansen", "Bakker", "Visser", "Smit", "Meijer", "de Boer", "Mulder")),
    "germany": (("Hans", "Thomas", "Michael", "Klaus", "Andreas", "Jürgen", "Peter", "Ralf"), ("Müller", "Schmidt", "Weber", "Wagner", "Becker", "Hoffmann", "Koch", "Richter")),
    "france": (("Jean", "Philippe", "Alain", "Michel", "Patrick", "Laurent", "Didier", "Franck"), ("Martin", "Bernard", "Thomas", "Robert", "Petit", "Durand", "Leroy", "Moreau")),
    "portugal": (("José", "João", "Manuel", "Carlos", "António", "Paulo", "Rui", "Fernando"), ("Silva", "Santos", "Ferreira", "Pereira", "Costa", "Oliveira", "Martins", "Sousa")),
    "brazil": (("Carlos", "Paulo", "José", "Luiz", "Marcos", "Sérgio", "Renato", "Roberto"), ("Silva", "Santos", "Oliveira", "Souza", "Pereira", "Costa", "Ferreira", "Almeida")),
    "argentina": (("Carlos", "Jorge", "Miguel", "Ricardo", "Oscar", "Héctor", "Daniel", "Marcelo"), ("González", "Rodríguez", "Fernández", "López", "Martínez", "Pérez", "Romero", "Díaz")),
    "colombia": (("Carlos", "Jorge", "Luis", "Óscar", "Hernán", "Alberto", "Eduardo", "Álvaro"), ("Gómez", "Rodríguez", "Martínez", "García", "López", "Ramírez", "Torres", "Rojas")),
    "mexico": (("José", "Juan", "Carlos", "Miguel", "Jorge", "Manuel", "Ricardo", "Héctor"), ("Hernández", "García", "Martínez", "López", "González", "Pérez", "Sánchez", "Ramírez")),
    "japan": (("Hiroshi", "Takashi", "Kenji", "Masato", "Koji", "Akira", "Takeshi", "Naoki"), ("Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe", "Ito", "Yamamoto", "Nakamura")),
    "usa": (("John", "Michael", "Robert", "David", "James", "Thomas", "Mark", "Scott"), ("Smith", "Johnson", "Williams", "Brown", "Miller", "Davis", "Wilson", "Moore")),
}

_GENERIC_POOL = (("Alex", "Martin", "Daniel", "Peter", "Victor", "Thomas", "Robert", "André"), ("Martin", "Novak", "Meyer", "Rossi", "Costa", "Petrov", "Jansen", "Kovac"))


def _country_key(country: str | None) -> str:
    text = str(country or "").strip().casefold()
    aliases = {
        "españa": "spain", "spain": "spain", "italia": "italy", "italy": "italy",
        "inglaterra": "england", "england": "england", "escocia": "scotland", "scotland": "scotland",
        "rusia": "russia", "russia": "russia", "bélgica": "belgium", "belgica": "belgium", "belgium": "belgium",
        "turquía": "turkey", "turquia": "turkey", "turkey": "turkey", "grecia": "greece", "greece": "greece",
        "países bajos": "netherlands", "paises bajos": "netherlands", "netherlands": "netherlands", "holanda": "netherlands",
        "alemania": "germany", "germany": "germany", "francia": "france", "france": "france",
        "portugal": "portugal", "brasil": "brazil", "brazil": "brazil", "argentina": "argentina",
        "colombia": "colombia", "méxico": "mexico", "mexico": "mexico", "japón": "japan", "japon": "japan", "japan": "japan",
        "estados unidos": "usa", "usa": "usa", "united states": "usa",
    }
    return aliases.get(text, "generic")


def _club_scale(team: dict[str, Any], strength: float) -> int:
    """Return a compact 1..5 organisational scale, not a sporting rating."""
    members = int(team.get("members") or 0)
    budget = int(team.get("budget") or 0)
    academy = int(team.get("academy_level") or 0)
    source_sd = int(team.get("sporting_director_level") or 0)
    score = 0
    score += 1 if strength >= 63 else 0
    score += 1 if strength >= 72 else 0
    score += 1 if members >= 8_000 or budget >= 300_000_000 else 0
    score += 1 if members >= 20_000 or budget >= 1_000_000_000 or academy >= 4 or source_sd >= 3 else 0
    return max(1, min(5, 1 + score))


def _skill_profile(role: str, *, base: int, rng: Random) -> dict[str, int]:
    values = {key: max(1, min(20, base + rng.randint(-3, 3))) for key in SKILL_LABELS}
    boosts: dict[str, tuple[str, ...]] = {
        "assistant_manager": ("tactical", "coaching", "discipline", "judging_player"),
        "first_team_coach": ("coaching", "youth", "tactical"),
        "goalkeeping_coach": ("goalkeeping", "coaching", "discipline"),
        "physio": ("physiotherapy", "discipline"),
        "scout": ("judging_player", "judging_potential", "market_knowledge"),
        "chief_scout": ("judging_player", "judging_potential", "market_knowledge", "discipline"),
        "sporting_director": ("negotiation", "market_knowledge", "judging_player", "discipline"),
    }
    for key in boosts.get(role, ()):
        values[key] = max(values[key], min(20, base + rng.randint(1, 4)))
    # Non-specialists should not accidentally rival a qualified physio/GK coach.
    if role != "physio":
        values["physiotherapy"] = min(values["physiotherapy"], 10)
    if role != "goalkeeping_coach":
        values["goalkeeping"] = min(values["goalkeeping"], 11)
    return values


def _generated_name(country: str | None, rng: Random, used: set[str]) -> str:
    firsts, surnames = _NAME_POOLS.get(_country_key(country), _GENERIC_POOL)
    for _ in range(32):
        name = f"{rng.choice(firsts)} {rng.choice(surnames)}"
        if name not in used:
            used.add(name)
            return name
    name = f"{rng.choice(firsts)} {rng.choice(surnames)} {len(used)+1}"
    used.add(name)
    return name


def _staff_roles_for_club(team: dict[str, Any], scale: int) -> list[str]:
    roles = ["assistant_manager", "first_team_coach", "physio", "scout"]
    if scale >= 2:
        roles.append("goalkeeping_coach")
    if scale >= 3:
        roles.append("first_team_coach")
        roles.append("chief_scout")
    source_sd = int(team.get("sporting_director_level") or 0)
    if source_sd > 0 or scale >= 3:
        roles.append("sporting_director")
    if scale >= 5:
        roles.extend(("first_team_coach", "scout"))
    return roles


def _generate_staff(team: dict[str, Any], *, seed: int, strength: float) -> list[dict[str, Any]]:
    team_id = int(team["source_id"])
    league = team.get("league") or {}
    country = str(league.get("country") or team.get("country") or "")
    scale = _club_scale(team, strength)
    rng = Random((int(seed) * 1_000_003) ^ (team_id * 97_409) ^ 0x9394)
    used: set[str] = set()
    role_counts: dict[str, int] = {}
    members: list[dict[str, Any]] = []
    for role in _staff_roles_for_club(team, scale):
        idx = role_counts.get(role, 0) + 1
        role_counts[role] = idx
        # Better-organised clubs tend to employ stronger staff, while leaving
        # enough variance for individual hires to matter later.
        base = max(6, min(15, 6 + round(scale * 1.5) + rng.randint(-2, 2)))
        if role == "sporting_director" and int(team.get("sporting_director_level") or 0) > 0:
            base = max(base, min(17, 8 + int(team.get("sporting_director_level") or 0) * 2))
        member_id = f"staff-{team_id}-{role}-{idx}"
        members.append({
            "id": member_id,
            "name": _generated_name(country, rng, used),
            "role": role,
            "role_label": STAFF_ROLES[role].label,
            "skills": _skill_profile(role, base=base, rng=rng),
            "generated": True,
            "provenance": "generated_career_staff",
            "provenance_label": "Generado por la carrera",
            "joined": "1993-07-01",
            "team_id": team_id,
            "active": True,
        })
    return members


def _eligible_members(members: list[dict[str, Any]], spec: dict[str, Any]) -> list[dict[str, Any]]:
    roles = set(spec.get("roles") or ())
    return [member for member in members if member.get("active", True) and member.get("role") in roles]


def _default_assignee(members: list[dict[str, Any]], spec: dict[str, Any]) -> str:
    desired = str(spec.get("default") or "manager")
    if desired == "manager":
        return "manager"
    eligible = _eligible_members(members, spec)
    preferred = next((m for m in eligible if m.get("role") == desired), None)
    if preferred:
        return str(preferred["id"])
    return str(eligible[0]["id"]) if eligible else "manager"


def ensure_club_staff_state(
    state: dict[str, Any],
    *,
    team: dict[str, Any],
    strength: float,
    game_date: date | None = None,
) -> dict[str, Any]:
    """Ensure a persistent staff structure exists for ``team`` in this save."""
    root = state.setdefault("club_staff", {})
    team_id = int(team["source_id"])
    key = str(team_id)
    club = root.get(key)
    if not isinstance(club, dict):
        club = {
            "schema": STAFF_SCHEMA_9394,
            "team_id": team_id,
            "created": (game_date or date(1993, 7, 1)).isoformat(),
            "members": _generate_staff(team, seed=int(state.get("seed") or 9394), strength=float(strength)),
            "responsibilities": {},
        }
        root[key] = club
    club.setdefault("schema", STAFF_SCHEMA_9394)
    club.setdefault("team_id", team_id)
    club.setdefault("members", [])
    assignments = club.setdefault("responsibilities", {})
    for resp_key, spec in RESPONSIBILITIES.items():
        if resp_key not in assignments:
            assignments[resp_key] = _default_assignee(club["members"], spec)
    return club


def _quality_label(value: int | None) -> str:
    if value is None:
        return "Decisión directa"
    if value >= 17:
        return "Excelente"
    if value >= 14:
        return "Fuerte"
    if value >= 11:
        return "Fiable"
    if value >= 8:
        return "Limitado"
    return "Débil"


def _load_label(count: int) -> str:
    if count <= 1:
        return "Ligera"
    if count <= 3:
        return "Normal"
    if count <= 5:
        return "Alta"
    return "Sobrecargado"


def club_staff_snapshot(
    state: dict[str, Any],
    *,
    team: dict[str, Any],
    strength: float,
    game_date: date | None = None,
) -> dict[str, Any]:
    club = ensure_club_staff_state(state, team=team, strength=strength, game_date=game_date)
    members = [dict(member) for member in club.get("members") or [] if member.get("active", True)]
    by_id = {str(member["id"]): member for member in members}
    workload: dict[str, int] = {member_id: 0 for member_id in by_id}
    manager_count = 0
    for assignee in (club.get("responsibilities") or {}).values():
        if assignee == "manager":
            manager_count += 1
        elif str(assignee) in workload:
            workload[str(assignee)] += 1

    member_rows: list[dict[str, Any]] = []
    for member in members:
        mid = str(member["id"])
        member_rows.append({
            **member,
            "skill_labels": {key: SKILL_LABELS[key] for key in SKILL_LABELS},
            "workload": workload.get(mid, 0),
            "workload_label": _load_label(workload.get(mid, 0)),
        })

    responsibility_rows: list[dict[str, Any]] = []
    for resp_key, spec in RESPONSIBILITIES.items():
        assignee = str((club.get("responsibilities") or {}).get(resp_key) or "manager")
        staff_member = by_id.get(assignee)
        skill = str(spec["skill"])
        raw_quality = None if assignee == "manager" else int((staff_member or {}).get("skills", {}).get(skill) or 0)
        # Multiple important responsibilities create a visible workload signal.
        # NF0 does not silently penalise results yet; later systems may consume
        # the effective value explicitly.
        load = manager_count if assignee == "manager" else workload.get(assignee, 0)
        effective = None if raw_quality is None else max(1, raw_quality - max(0, load - 3))
        eligible = [{"id": "manager", "name": "Tú (mánager)", "role": "manager", "role_label": "Mánager"}]
        eligible.extend({"id": str(m["id"]), "name": m["name"], "role": m["role"], "role_label": m["role_label"]} for m in _eligible_members(members, spec))
        responsibility_rows.append({
            "key": resp_key,
            "label": spec["label"],
            "area": spec["area"],
            "description": spec["description"],
            "skill": skill,
            "skill_label": SKILL_LABELS[skill],
            "assignee": assignee,
            "assignee_name": "Tú (mánager)" if assignee == "manager" else str((staff_member or {}).get("name") or "Responsable no disponible"),
            "assignee_role": "Mánager" if assignee == "manager" else str((staff_member or {}).get("role_label") or "—"),
            "quality": effective,
            "quality_label": _quality_label(effective),
            "workload": load,
            "workload_label": _load_label(load),
            "mode": "direct" if assignee == "manager" else "delegated",
            "mode_label": "Control directo" if assignee == "manager" else "Delegado",
            "workspace": str(spec.get("workspace") or "home"),
            "effect": str(spec.get("effect") or "Afecta a la calidad operativa de esta tarea."),
            "eligible_assignees": eligible,
        })

    return {
        "schema": STAFF_SCHEMA_9394,
        "team_id": int(team["source_id"]),
        "team_name": str(team.get("name") or team.get("long_name") or team["source_id"]),
        "members": member_rows,
        "responsibilities": responsibility_rows,
        "manager_responsibility_count": manager_count,
        "generated_count": sum(1 for member in members if member.get("generated")),
        "provenance_note": "Los empleados sin fuente histórica individual son generados por la carrera y se etiquetan como tales.",
    }



def responsibility_effectiveness(
    state: dict[str, Any],
    *,
    team: dict[str, Any],
    strength: float,
    responsibility_key: str,
    game_date: date | None = None,
) -> dict[str, Any]:
    """Return the explicit operational quality for one delegated duty.

    This is the bridge from NF0 into the rest of the simulation.  Consumers
    must use this payload rather than reading a staff attribute directly, so
    workload and direct-manager ownership are handled consistently.
    """
    key = str(responsibility_key)
    if key not in RESPONSIBILITIES:
        raise KeyError(f"responsabilidad desconocida: {key}")
    snap = club_staff_snapshot(state, team=team, strength=strength, game_date=game_date)
    row = next(item for item in snap["responsibilities"] if item["key"] == key)
    if row["assignee"] == "manager":
        # The user's own work is competent but not magically specialist. Heavy
        # self-management also has a visible cost, preserving the value of
        # building a good staff without forcing delegation.
        load = int(row.get("workload") or 0)
        quality = max(8, 14 - max(0, load - 5))
        source = "manager_direct"
        name = "Tú (mánager)"
    else:
        quality = max(1, min(20, int(row.get("quality") or 1)))
        source = "delegated_staff"
        name = str(row.get("assignee_name") or "Responsable")
    confidence = max(35, min(96, 38 + quality * 3))
    return {
        "responsibility": key,
        "assignee": row["assignee"],
        "assignee_name": name,
        "assignee_role": row.get("assignee_role"),
        "skill": row.get("skill"),
        "quality": quality,
        "quality_label": _quality_label(quality),
        "workload": int(row.get("workload") or 0),
        "workload_label": row.get("workload_label"),
        "confidence": confidence,
        "source": source,
    }

def assign_responsibility(
    state: dict[str, Any],
    *,
    team: dict[str, Any],
    strength: float,
    responsibility_key: str,
    assignee: str,
    game_date: date | None = None,
) -> dict[str, Any]:
    key = str(responsibility_key)
    if key not in RESPONSIBILITIES:
        raise KeyError(f"responsabilidad desconocida: {key}")
    club = ensure_club_staff_state(state, team=team, strength=strength, game_date=game_date)
    assignee = str(assignee)
    if assignee != "manager":
        member = next((m for m in club.get("members") or [] if str(m.get("id")) == assignee and m.get("active", True)), None)
        if member is None:
            raise ValueError("el empleado seleccionado no pertenece al cuerpo técnico activo")
        allowed_roles = set(RESPONSIBILITIES[key].get("roles") or ())
        if member.get("role") not in allowed_roles:
            raise ValueError(f"{member.get('role_label') or member.get('role')} no es elegible para esta responsabilidad")
    club.setdefault("responsibilities", {})[key] = assignee
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    return club_staff_snapshot(state, team=team, strength=strength, game_date=game_date)
