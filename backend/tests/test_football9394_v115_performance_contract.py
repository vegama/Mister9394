from __future__ import annotations

import copy
from datetime import date

from backend.app.football9394 import manager_career as manager_module
from backend.app.football9394.manager_career import ManagerCareerRuntime9394


def _fresh_career(seed: int = 11501) -> ManagerCareerRuntime9394:
    return ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=seed, through_matchday=0)


def test_v115_quiet_daily_advance_does_not_rebuild_every_roster(monkeypatch):
    career = _fresh_career()
    calls = 0
    original = career._rebuild_rosters

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(career, "_rebuild_rosters", counted)
    for _ in range(5):
        result = career.advance_day()
        assert result.get("requires_match") is not True

    # The historical world can progress without recreating 12k player rows on
    # every daily tournament/special-competition tick.
    assert calls == 0


def test_v115_loading_persisted_career_reuses_player_dynamics(monkeypatch):
    state = copy.deepcopy(_fresh_career(seed=11502).state)
    assert state.get("player_dynamics")
    calls = 0

    def unexpected_sync(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("persisted dynamics should not be globally recomputed on load")

    monkeypatch.setattr(manager_module, "sync_team_dynamics", unexpected_sync)
    restored = ManagerCareerRuntime9394(state)
    assert restored.state["career_id"] == state["career_id"]
    assert calls == 0


def test_v115_loading_migrated_finances_does_not_recompute_all_club_baselines(monkeypatch):
    state = copy.deepcopy(_fresh_career(seed=11503).state)
    assert state.get("club_finances")
    calls = 0

    def unexpected_finance(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("fully migrated club finances should be reused on load")

    monkeypatch.setattr(manager_module, "initial_club_finances", unexpected_finance)
    restored = ManagerCareerRuntime9394(state)
    assert restored.state["club_finances"] == state["club_finances"]
    assert calls == 0


def test_v115_prepare_match_commits_draft_selection_and_tactics_in_one_request(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp

    monkeypatch.setattr(webapp, "CAREER_SAVE_ROOT", tmp_path)
    with TestClient(webapp.app) as client:
        created = client.post("/api/football9394/careers", json={"team_id":16,"league_id":1,"seed":11504,"through_matchday":7})
        assert created.status_code == 200
        cid = created.json()["career_id"]
        advanced = client.post(f"/api/football9394/careers/{cid}/advance")
        assert advanced.status_code == 200 and advanced.json()["requires_match"] is True
        selection = advanced.json()["career"]["selection"]
        response = client.post(
            f"/api/football9394/careers/{cid}/live/start",
            json={
                "tactics":{"formation":"4-3-3","mentality":"attacking"},
                "starter_ids":selection["starter_ids"],
                "bench_ids":selection["bench_ids"],
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["match"]["status"] in {"preview", "live"}
        # Preparing the preview is a hot frontend path: do not duplicate the
        # whole career snapshot in the response after we just persisted it.
        assert "career" not in payload
        assert len(response.content) < 60_000
        persisted = client.get(f"/api/football9394/careers/{cid}").json()
        assert persisted["tactics"]["formation"] == "4-3-3"
        assert persisted["selection"]["starter_ids"] == selection["starter_ids"]


def test_v115_live_ticks_use_compact_payload_and_server_side_event_jump(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp

    monkeypatch.setattr(webapp, "CAREER_SAVE_ROOT", tmp_path)
    with TestClient(webapp.app) as client:
        created = client.post("/api/football9394/careers", json={"team_id":16,"league_id":1,"seed":11505,"through_matchday":7}).json()
        cid = created["career_id"]
        advanced = client.post(f"/api/football9394/careers/{cid}/advance").json()
        selection = advanced["career"]["selection"]
        started = client.post(f"/api/football9394/careers/{cid}/live/start", json={"starter_ids":selection["starter_ids"],"bench_ids":selection["bench_ids"]})
        assert started.status_code == 200
        tick = client.post(f"/api/football9394/careers/{cid}/live/advance", json={"minutes":5})
        assert tick.status_code == 200
        assert "career" not in tick.json()
        assert len(tick.content) < 60_000
        before = int(tick.json()["match"]["minute"] or 0)
        jump = client.post(f"/api/football9394/careers/{cid}/live/advance", json={"minutes":20,"until_event":True})
        assert jump.status_code == 200
        assert "career" not in jump.json()
        assert len(jump.content) < 60_000
        assert int(jump.json()["match"]["minute"] or 0) >= before


def test_v115_competition_ui_window_does_not_ship_full_season(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp

    monkeypatch.setattr(webapp, "CAREER_SAVE_ROOT", tmp_path)
    with TestClient(webapp.app) as client:
        state = client.post("/api/football9394/careers", json={"team_id":16,"league_id":1,"seed":11506,"through_matchday":7}).json()
        cid = state["career_id"]
        compact = client.get(f"/api/football9394/careers/{cid}/competitions/league/1?results_limit=24&calendar_limit=28")
        assert compact.status_code == 200
        payload = compact.json()
        assert len(payload.get("results") or []) <= 24
        assert len(payload.get("calendar") or []) <= 28
        assert len(compact.content) < 40_000


def test_v115_career_snapshot_does_not_duplicate_player_dossiers():
    import json
    career = _fresh_career(seed=11507)
    payload = career.snapshot()
    encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    assert len(encoded) < 150_000
    assert "starters" not in payload["selection"]
    assert "bench" not in payload["selection"]
    assert payload["squad"]
    assert "match_history" not in payload["squad"][0]
    assert "attributes" not in payload["squad"][0]
    assert "tactical_fit" in payload["squad"][0]


def test_v115_selection_and_tactics_mutations_return_only_changed_slice(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp

    monkeypatch.setattr(webapp, "CAREER_SAVE_ROOT", tmp_path)
    with TestClient(webapp.app) as client:
        created = client.post("/api/football9394/careers", json={"team_id":16,"league_id":1,"seed":11508,"through_matchday":0}).json()
        cid = created["career_id"]
        selection = created["selection"]
        response = client.put(
            f"/api/football9394/careers/{cid}/selection?compact=true",
            json={"starter_ids":selection["starter_ids"],"bench_ids":selection["bench_ids"],"auto_select":False},
        )
        assert response.status_code == 200
        assert set(response.json()) == {"selection"}
        assert len(response.content) < 5_000

        tactics = dict(created["tactics"])
        tactics["formation"] = "4-3-3"
        response = client.put(f"/api/football9394/careers/{cid}/tactics?compact=true", json=tactics)
        assert response.status_code == 200
        assert set(response.json()) == {"tactics", "tactical_identity"}
        assert len(response.content) < 5_000


def test_v115_repeated_api_load_reuses_validated_runtime(monkeypatch, tmp_path):
    import backend.app.football9394.webapp as webapp
    from backend.app.football9394.manager_route_support import _clear_runtime_cache, _load_manager_career
    from backend.app.football9394.manager_career import ManagerCareerStore9394

    monkeypatch.setattr(webapp, "CAREER_SAVE_ROOT", tmp_path)
    _clear_runtime_cache()
    career = _fresh_career(seed=11509)
    store = ManagerCareerStore9394(tmp_path)
    store.save(career.state)

    first = _load_manager_career(career.state["career_id"])
    second = _load_manager_career(career.state["career_id"])
    assert second is first

    # A save made with another state object must invalidate the runtime cache,
    # so external/manual save changes are never hidden by the hot-path cache.
    replacement = copy.deepcopy(first.state)
    replacement["current_date"] = "1993-09-01"
    store.save(replacement)
    third = _load_manager_career(career.state["career_id"])
    assert third is not first
    assert third.state["current_date"] == "1993-09-01"
    _clear_runtime_cache()


def test_v115_market_search_avoids_per_candidate_team_resolution(monkeypatch):
    career = _fresh_career(seed=11510)
    calls = 0
    original = career._current_team_id

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(career, "_current_team_id", counted)
    rows = career.search_market("", limit=30)
    assert len(rows) == 30
    # Team resolution is still needed while expanding the final dossier rows,
    # but not while filtering/ranking all 12k candidates.
    assert calls <= 40


def test_v115_partial_finance_migration_only_builds_missing_rows(monkeypatch):
    state = copy.deepcopy(_fresh_career(seed=11511).state)
    universe = manager_module.default_runtime_snapshot()
    controlled = int(state["team_id"])
    missing = next(
        int(team["source_id"])
        for team in universe.payload.get("teams", [])
        if int(team["source_id"]) != controlled
    )
    state["club_finances"].pop(str(missing), None)
    calls: list[int] = []
    original = manager_module.initial_club_finances

    def counted(team, *args, **kwargs):
        calls.append(int(team.get("source_id") or 0))
        return original(team, *args, **kwargs)

    monkeypatch.setattr(manager_module, "initial_club_finances", counted)
    restored = ManagerCareerRuntime9394(state, universe=universe)
    assert str(missing) in restored.state["club_finances"]
    assert calls == [missing]


def test_v115_live_tick_uses_durable_overlay_without_rewriting_full_save(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp
    from backend.app.football9394.manager_route_support import _clear_runtime_cache

    monkeypatch.setattr(webapp, "CAREER_SAVE_ROOT", tmp_path)
    _clear_runtime_cache()
    with TestClient(webapp.app) as client:
        created = client.post(
            "/api/football9394/careers",
            json={"team_id":16,"league_id":1,"seed":11512,"through_matchday":7},
        ).json()
        cid = created["career_id"]
        advanced = client.post(f"/api/football9394/careers/{cid}/advance").json()
        selection = advanced["career"]["selection"]
        started = client.post(
            f"/api/football9394/careers/{cid}/live/start",
            json={"starter_ids":selection["starter_ids"],"bench_ids":selection["bench_ids"]},
        )
        assert started.status_code == 200
        save_path = tmp_path / f"{cid}.json"
        base_bytes = save_path.read_bytes()
        base_stat = save_path.stat()

        tick = client.post(f"/api/football9394/careers/{cid}/live/advance", json={"minutes":5})
        assert tick.status_code == 200
        minute = int(tick.json()["match"]["minute"] or 0)
        assert minute >= 5
        assert save_path.read_bytes() == base_bytes
        assert save_path.stat().st_mtime_ns == base_stat.st_mtime_ns
        overlay = tmp_path / f"{cid}.hot.json"
        assert overlay.is_file()
        assert overlay.stat().st_size < 200_000

        # Simulate a process restart: both in-memory caches disappear, but the
        # exact in-match checkpoint must be replayed over the full save.
        _clear_runtime_cache()
        resumed = client.get(f"/api/football9394/careers/{cid}/live")
        assert resumed.status_code == 200
        assert int(resumed.json()["minute"] or 0) == minute

        # A complete save consolidates the overlay and removes the derivative
        # checkpoint only after the canonical save+backup publish succeeds.
        live = resumed.json()
        while str(live.get("status") or "") != "finished":
            progressed = client.post(f"/api/football9394/careers/{cid}/live/advance", json={"minutes":15})
            assert progressed.status_code == 200
            live = progressed.json()["match"]
        result = client.post(f"/api/football9394/careers/{cid}/live/finish")
        assert result.status_code == 200
        assert not overlay.exists()
    _clear_runtime_cache()


def test_v115_neutral_daily_recovery_skips_equilibrium_rows(monkeypatch):
    from backend.app.football9394 import development as development_module

    state = development_module.initial_player_development(
        [{"source_id": pid, "overall": 60 + (pid % 20)} for pid in range(1, 401)]
    )
    calls = 0
    original = development_module.recover_medical_day

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(development_module, "recover_medical_day", counted)
    changed = development_module.recover_one_day(state, game_date=date(1993, 7, 2))
    assert changed is False
    assert calls == 0
    assert all(row["condition"] == 100 and row["form"] == 70 for row in state.values())


def test_v115_background_calendar_is_lazy_until_a_round_is_due(monkeypatch):
    career = _fresh_career(seed=11513)
    calls = 0
    original = career._league_schedule

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(career, "_league_schedule", counted)
    career._process_background_leagues_for_day(date(1993, 7, 2))
    assert calls == 0


def test_v115_compact_selection_and_tactics_survive_restart_without_full_save(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp
    from backend.app.football9394.manager_route_support import _clear_runtime_cache

    monkeypatch.setattr(webapp, "CAREER_SAVE_ROOT", tmp_path)
    _clear_runtime_cache()
    with TestClient(webapp.app) as client:
        created = client.post(
            "/api/football9394/careers",
            json={"team_id":16,"league_id":1,"seed":11514,"through_matchday":0},
        ).json()
        cid = created["career_id"]
        save_path = tmp_path / f"{cid}.json"
        original_bytes = save_path.read_bytes()
        original_stat = save_path.stat()

        selected = client.put(
            f"/api/football9394/careers/{cid}/selection?compact=true",
            json={"auto_select": True},
        )
        assert selected.status_code == 200
        tactics = client.put(
            f"/api/football9394/careers/{cid}/tactics?compact=true",
            json={"formation":"4-3-3","mentality":"balanced","tempo":"normal","pressing":"medium","directness":"mixed","defensive_line":"medium","marking":"zonal","width":"normal","offside_trap":False,"build_up":"balanced","final_third":"mixed","transition":"balanced"},
        )
        assert tactics.status_code == 200
        assert save_path.read_bytes() == original_bytes
        assert save_path.stat().st_mtime_ns == original_stat.st_mtime_ns
        overlay = tmp_path / f"{cid}.hot.json"
        assert overlay.is_file()
        assert overlay.stat().st_size < 200_000

        expected_selection = selected.json()["selection"]
        _clear_runtime_cache()
        restored = client.get(f"/api/football9394/careers/{cid}")
        assert restored.status_code == 200
        payload = restored.json()
        assert payload["selection"]["starter_ids"] == expected_selection["starter_ids"]
        assert payload["selection"]["bench_ids"] == expected_selection["bench_ids"]
        assert payload["tactics"]["formation"] == "4-3-3"
    _clear_runtime_cache()


def test_v115_live_start_uses_redundant_boundary_overlay_and_recovers_corruption(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp
    from backend.app.football9394.manager_route_support import _career_store, _clear_runtime_cache, _load_manager_career

    monkeypatch.setattr(webapp, "CAREER_SAVE_ROOT", tmp_path)
    _clear_runtime_cache()
    with TestClient(webapp.app) as client:
        created = client.post(
            "/api/football9394/careers",
            json={"team_id":16,"league_id":1,"seed":11515,"through_matchday":7},
        ).json()
        cid = created["career_id"]
        advanced = client.post(f"/api/football9394/careers/{cid}/advance").json()
        selection = advanced["career"]["selection"]
        save_path = tmp_path / f"{cid}.json"
        canonical_bytes = save_path.read_bytes()
        canonical_mtime = save_path.stat().st_mtime_ns

        started = client.post(
            f"/api/football9394/careers/{cid}/live/start",
            json={"starter_ids":selection["starter_ids"],"bench_ids":selection["bench_ids"]},
        )
        assert started.status_code == 200
        assert save_path.read_bytes() == canonical_bytes
        assert save_path.stat().st_mtime_ns == canonical_mtime
        overlay = tmp_path / f"{cid}.hot.json"
        backup = overlay.with_suffix(overlay.suffix + ".bak")
        assert overlay.is_file() and backup.is_file()
        assert overlay.stat().st_size < 200_000 and backup.stat().st_size < 200_000

        # Damage the primary derivative checkpoint. Recovery must fall back to
        # the independent overlay backup instead of losing the match boundary.
        overlay.write_text("{broken", encoding="utf-8")
        _clear_runtime_cache()
        resumed = client.get(f"/api/football9394/careers/{cid}/live")
        assert resumed.status_code == 200
        assert resumed.json()["status"] in {"preview", "live"}
        assert int(resumed.json()["minute"] or 0) == 0

        # The next canonical save folds the recovered state into the career and
        # removes both the overlay ladder and any quarantined corrupt fragment.
        runtime = _load_manager_career(cid)
        _career_store().save(runtime.state)
        assert not list(tmp_path.glob(f"{cid}.hot.json*"))
    _clear_runtime_cache()


def test_v115_compact_market_workflow_uses_redundant_overlay_and_survives_restart(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    import backend.app.football9394.webapp as webapp
    from backend.app.football9394.manager_route_support import _clear_runtime_cache

    monkeypatch.setattr(webapp, "CAREER_SAVE_ROOT", tmp_path)
    _clear_runtime_cache()
    with TestClient(webapp.app) as client:
        created = client.post(
            "/api/football9394/careers",
            json={"team_id":16,"league_id":1,"seed":11516,"through_matchday":0},
        ).json()
        cid = created["career_id"]
        save_path = tmp_path / f"{cid}.json"
        canonical_bytes = save_path.read_bytes()
        canonical_mtime = save_path.stat().st_mtime_ns
        market = client.get(f"/api/football9394/careers/{cid}/market?limit=80").json()
        target = next(
            row for row in market
            if int(row.get("team_id") or 0) != 16 and str(row.get("nationality") or "") == "España"
        )
        pid = int(target["id"])
        own_pid = int(created["squad"][0]["id"])
        original_trust = int(created["squad"][0]["manager_relationship"]["trust"])

        watched = client.post(
            f"/api/football9394/careers/{cid}/watchlist/{pid}?compact=true",
            json={"watched": True},
        )
        assert watched.status_code == 200
        inquiry = client.post(f"/api/football9394/careers/{cid}/market-inquiry/{pid}?compact=true")
        assert inquiry.status_code == 200
        listed = client.post(
            f"/api/football9394/careers/{cid}/transfer-list/{own_pid}?compact=true",
            json={"asking_price": 1_000_000},
        )
        assert listed.status_code == 200
        negotiation = client.post(
            f"/api/football9394/careers/{cid}/negotiations?compact=true",
            json={
                "player_id":pid,"fee_offer":0,"salary_offer":0,"contract_years":3,
                "squad_role":"rotation","signing_bonus":0,"deal_type":"transfer","loan_wage_share":100,
            },
        )
        assert negotiation.status_code == 200
        negotiation_id = negotiation.json()["negotiation"]["id"]
        assert save_path.read_bytes() == canonical_bytes
        assert save_path.stat().st_mtime_ns == canonical_mtime
        overlay = tmp_path / f"{cid}.hot.json"
        backup = overlay.with_suffix(overlay.suffix + ".bak")
        assert overlay.is_file() and backup.is_file()
        assert overlay.stat().st_size < 200_000

        _clear_runtime_cache()
        flow = client.get(f"/api/football9394/careers/{cid}/market-flow")
        assert flow.status_code == 200
        payload = flow.json()
        assert pid in payload["watchlist"]
        assert any(int(row.get("player_id") or 0) == pid for row in payload["inquiries"])
        assert any(int(row.get("player_id") or 0) == own_pid for row in payload["listings"])
        assert any(str(row.get("id") or "") == negotiation_id for row in payload["negotiations"])
        player = client.get(f"/api/football9394/careers/{cid}/players/{own_pid}")
        assert player.status_code == 200
        assert int(player.json()["manager_relationship"]["trust"]) == original_trust - 12

        # A real world boundary consolidates the tiny workflow overlay into the
        # canonical save and cleans the derivative recovery ladder.
        advanced = client.post(f"/api/football9394/careers/{cid}/advance")
        assert advanced.status_code == 200
        assert not list(tmp_path.glob(f"{cid}.hot.json*"))
    _clear_runtime_cache()
