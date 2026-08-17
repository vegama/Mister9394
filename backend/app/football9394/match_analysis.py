from __future__ import annotations

"""NF8 pre/live/post match interpretation with causal, football-facing language."""

from typing import Any


def live_player_performance(snapshot: dict[str, Any], *, controlled_team_id: int) -> list[dict[str, Any]]:
    own_home = int(snapshot.get("home_team_id") or 0) == int(controlled_team_id)
    ids = list(snapshot.get("home_on_pitch_ids") if own_home else snapshot.get("away_on_pitch_ids") or [])
    events = list(snapshot.get("events") or [])
    fatigue = dict(snapshot.get("home_fatigue") if own_home else snapshot.get("away_fatigue") or {})
    rows=[]
    for pid in ids:
        score = 6.5
        positives=[]; negatives=[]
        for event in events:
            if str(event.get("player_id")) != str(pid):
                continue
            kind=event.get("kind")
            if kind == "goal": score += 1.1; positives.append("gol")
            elif kind == "assist": score += .7; positives.append("asistencia")
            elif kind in {"save", "penalty_saved"}: score += .25
            elif kind in {"yellow"}: score -= .25; negatives.append("amonestado")
            elif kind in {"red", "second_yellow_red"}: score -= 1.6; negatives.append("expulsado")
            elif kind == "defensive_error": score -= .65; negatives.append("error defensivo")
        f=float(fatigue.get(str(pid),0.0)); score -= max(0.0, f-45.0)/90.0
        rows.append({"player_id":int(pid),"rating":round(max(3.5,min(9.8,score)),1),"fatigue":round(f,1),"positives":positives,"negatives":negatives})
    return sorted(rows,key=lambda r:(-r["rating"],r["player_id"]))


def bench_advice(snapshot: dict[str, Any], *, controlled_team_id: int, staff_quality: int) -> list[dict[str, Any]]:
    own_home=int(snapshot.get("home_team_id") or 0)==int(controlled_team_id)
    own=dict(snapshot.get("home") if own_home else snapshot.get("away") or {})
    opp=dict(snapshot.get("away") if own_home else snapshot.get("home") or {})
    tactics=dict(snapshot.get("home_tactics") if own_home else snapshot.get("away_tactics") or {})
    minute=int(snapshot.get("minute") or 0); advice=[]
    quality=max(1,min(20,int(staff_quality)))
    def add(kind,title,detail,change=None,priority="normal"):
        advice.append({"kind":kind,"title":title,"detail":detail,"suggested_change":change,"priority":priority})
    if minute >= 20 and int(opp.get("shots") or 0) >= int(own.get("shots") or 0)+4:
        add("territory","El rival está llegando demasiado","Está acumulando más remates; conviene proteger mejor la pérdida o bajar el riesgo.",{"mentality":"balanced","defensive_line":"low"},"high")
    if minute >= 25 and int(own.get("possession") or 50) <= 40 and quality >= 9:
        add("possession","Nos cuesta conservar la pelota","Podemos dar una salida más corta y bajar un punto el ritmo.",{"build_up":"patient","tempo":"slow"})
    if minute >= 50 and int(own.get("shots") or 0) >= int(opp.get("shots") or 0)+5 and int(own.get("goals") or 0) <= int(opp.get("goals") or 0) and quality >= 12:
        add("conversion","Llegamos, pero no convertimos","No hace falta romper el plan: busca más presencia en área antes de subir aún más el riesgo.",{"final_third":"crosses"})
    fatigue = snapshot.get("controlled_on_pitch") or []
    tired=[p for p in fatigue if float(p.get("match_fatigue") or 0)>=42]
    if tired:
        add("fatigue",f"{len(tired)} jugador{'es' if len(tired)!=1 else ''} muy cargado{'s' if len(tired)!=1 else ''}","Valora un cambio: la fatiga ya está reduciendo su rendimiento.",None,"high" if any(float(p.get("match_fatigue") or 0)>=55 for p in tired) else "normal")
    if not advice and minute >= 15:
        add("stable","El partido no exige un cambio claro","Mantendría el plan y observaría la siguiente secuencia antes de tocar estructura.")
    return advice[:4]


def postmatch_diagnosis(snapshot: dict[str, Any], *, controlled_team_id: int, familiarity: float = 70.0) -> dict[str, Any]:
    own_home=int(snapshot.get("home_team_id") or 0)==int(controlled_team_id)
    own=dict(snapshot.get("home") if own_home else snapshot.get("away") or {})
    opp=dict(snapshot.get("away") if own_home else snapshot.get("home") or {})
    tactics=dict(snapshot.get("home_tactics") if own_home else snapshot.get("away_tactics") or {})
    gf=int(own.get("goals") or 0); ga=int(opp.get("goals") or 0)
    facts=[f"Remates {int(own.get('shots') or 0)}-{int(opp.get('shots') or 0)}",f"Posesión {int(own.get('possession') or 0)}%-{int(opp.get('possession') or 0)}%",f"Córners {int(own.get('corners') or 0)}-{int(opp.get('corners') or 0)}"]
    reasons=[]
    shot_diff=int(own.get("shots") or 0)-int(opp.get("shots") or 0)
    if shot_diff >= 5 and gf <= ga:
        reasons.append("El equipo produjo más volumen que el rival, pero la finalización no convirtió esa superioridad en marcador.")
    elif shot_diff <= -5:
        reasons.append("El rival generó más ataques terminados; la principal señal es territorial y defensiva, no sólo de acierto.")
    if int(own.get("possession") or 50) < 42 and tactics.get("build_up") == "patient":
        reasons.append("La salida paciente no consiguió estabilizar la posesión ante la presión rival.")
    if int(own.get("corners") or 0) >= 6 and gf == 0:
        reasons.append("Hubo volumen a balón parado sin recompensa; merece revisar lanzadores y rutina.")
    if float(familiarity) < 60:
        reasons.append("El plan todavía tiene poca familiaridad y eso reduce la precisión con la que se ejecutan las órdenes.")
    if not reasons:
        reasons.append("El resultado encaja con un partido relativamente equilibrado; no aparece una causa única que justifique rehacer el plan.")
    verdict="Victoria" if gf>ga else "Empate" if gf==ga else "Derrota"
    return {"verdict":verdict,"score":f"{gf}-{ga}","facts":facts,"reasons":reasons[:4],"next_actions":["Revisar carga de los titulares","Comprobar promesas y satisfacción tras los minutos","Actualizar preparación del siguiente rival"]}
