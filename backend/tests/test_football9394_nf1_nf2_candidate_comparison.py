from __future__ import annotations

"""La comparación A/B/C compara informes, no la verdad del simulador.

El plan de profundidad la pide en NF1 y en NF2 y no existía en ninguno. Lo que
estas pruebas fijan no es que ordene bien una lista, sino que respete la regla
que sostiene todo el ojeo: el club decide con lo que sabe, y cuando no sabe lo
bastante hay que decirlo en vez de fabricar una certeza.
"""

from datetime import date

from backend.app.football9394.candidate_comparison import build_view, compare

HOY = date(1994, 3, 1)


def vista(nombre, media, nivel, confianza, actualizado="1994-02-20", pid=None):
    return build_view(
        {"source_id": pid if pid is not None else abs(hash(nombre)) % 10000,
         "display_name": nombre, "overall": media, "broad_position": "DEL"},
        {"level": nivel, "confidence": confianza, "updated_on": actualizado},
        today=HOY,
    )


def test_menos_conocimiento_es_mas_horquilla():
    fiable = vista("Fiable", 78, 4, 80)
    de_oidas = vista("De oídas", 78, 1, 30)
    assert (fiable.high - fiable.low) < (de_oidas.high - de_oidas.low)
    # Y la misma media estimada no significa el mismo riesgo.
    assert fiable.estimate == de_oidas.estimate


def test_no_declara_ganador_cuando_las_horquillas_se_solapan():
    salida = compare([vista("Conocido", 78, 3, 72), vista("Dudoso", 81, 1, 30)])
    assert salida["undecidable"] is True
    assert "no se puede separar" in salida["verdict"]


def test_declara_diferencia_solo_cuando_el_peor_caso_gana():
    # 88 con informe profundo contra 70 bien conocido: no hay solape posible.
    salida = compare([vista("Crack", 88, 4, 90), vista("Discreto", 70, 4, 90)])
    assert salida["undecidable"] is False
    assert "destaca" in salida["verdict"]


def test_un_informe_viejo_pierde_precision_y_pide_revision():
    reciente = vista("Reciente", 76, 3, 70, actualizado="1994-02-20")
    viejo = vista("Viejo", 76, 3, 70, actualizado="1993-08-01")
    assert viejo.stale and not reciente.stale
    assert (viejo.high - viejo.low) > (reciente.high - reciente.low)
    assert viejo.confidence < reciente.confidence
    acciones = compare([reciente, viejo])["actions"]
    assert any(a["action"] == "rescout" for a in acciones)


def test_sin_conocimiento_no_se_inventa_nada():
    ciego = build_view({"source_id": 9, "display_name": "Desconocido", "overall": 70}, None, today=HOY)
    assert ciego.knowledge == 0
    assert ciego.high - ciego.low == 28
    acciones = compare([ciego, vista("Conocido", 70, 4, 90)])["actions"]
    assert any(a["action"] == "scout" and a["player_id"] == 9 for a in acciones)


def test_sin_candidatos_no_revienta():
    salida = compare([])
    assert salida["candidates"] == [] and salida["actions"] == []


def test_no_filtra_la_media_real_del_simulador():
    """La comparacion usa la horquilla del mercado, no el atributo oculto.

    Es la prueba que mas importa de todo el modulo. Al construirlo con la fila
    cruda del universo, Dubovsky salia con 74 -su media real- cuando el club solo
    podia estimar 71. Eso convertia una herramienta de decision en una filtracion.
    """
    from fastapi.testclient import TestClient
    from backend.app.football9394.webapp import app

    client = TestClient(app)
    career = client.post("/api/football9394/careers", json={
        "team_id": 16, "league_id": 1, "seed": 11, "through_matchday": 7}).json()["career_id"]
    market = client.get(f"/api/football9394/careers/{career}/market").json()[:3]
    salida = client.post(f"/api/football9394/careers/{career}/scouting/compare",
                         json={"player_ids": [row["id"] for row in market]}).json()

    por_id = {row["id"]: row for row in market}
    for candidato in salida["candidates"]:
        publico = por_id[candidato["player_id"]]
        low, high = publico["overall_range"]
        assert candidato["range"] == {"low": low, "high": high}
        # El conocimiento y el ojeador salen del mercado, no de cero.
        assert candidato["knowledge"] == publico["scout"]["level"]
        assert candidato["scout"] == publico["scout"]["observer"]

