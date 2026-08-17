from __future__ import annotations

"""NF11 · Causal information world: fact -> rumour -> news -> reaction -> consequence."""

from datetime import date, timedelta
from typing import Any


RUMOUR_KINDS = {"market_inquiry", "transfer_negotiation_opened", "incoming_transfer_offer", "manager_application", "manager_interest"}
PUBLIC_FACT_KINDS = {"ai_transfer", "user_transfer", "user_sale", "manager_change", "competition_completed", "training_injury", "contract_expired", "career_record", "board_sale_pressure", "board_sale_pressure_resolved", "financial_restructuring"}


def ensure_information_state(state: dict[str, Any]) -> None:
    state.setdefault("information_threads", [])
    state.setdefault("information_seen_keys", [])
    state.setdefault("media_reputation", {"credibility": 50, "pressure": 35, "relationship": 50})


def _event_key(event: dict[str, Any]) -> str:
    parts = [event.get("kind"), event.get("date"), event.get("player_id"), event.get("team_id"), event.get("from_team_id"), event.get("to_team_id"), event.get("buyer_team_id"), event.get("application_id"), event.get("negotiation_id")]
    return "|".join("" if value is None else str(value) for value in parts)


def register_information_event(state: dict[str, Any], event: dict[str, Any], *, headline: str = "", detail: str = "", news_id: str | None = None) -> dict[str, Any] | None:
    ensure_information_state(state)
    key = _event_key(event)
    kind = str(event.get("kind") or "fact")
    player_id = event.get("player_id")
    team_id = event.get("team_id") or event.get("to_team_id") or event.get("buyer_team_id")
    # Related market events stay in one story. An enquiry can become a
    # negotiation and later a confirmed transfer; those are stages of the same
    # history, not three unrelated headlines.
    if player_id is not None and kind in {"transfer_negotiation_opened", "user_transfer", "user_sale", "ai_transfer"}:
        related = next((row for row in reversed(state.get("information_threads") or []) if int((row.get("fact") or {}).get("entity",{}).get("player_id") or -1)==int(player_id) and row.get("origin_kind") in RUMOUR_KINDS and row.get("stage") not in {"cooled"}), None)
        if related:
            related.setdefault("consequences", []).append({"date": str(event.get("date") or state.get("current_date") or ""), "kind": kind, "team_id": team_id})
            if kind in {"user_transfer", "user_sale", "ai_transfer"}:
                related["confirmed_fact"] = {"kind": kind, "entity": {k: event.get(k) for k in ("player_id", "team_id", "from_team_id", "to_team_id", "buyer_team_id") if event.get(k) is not None}}
                related["certainty"] = 100
                if news_id:
                    related["news"] = {"id": news_id, "headline": headline, "detail": detail, "date": event.get("date")}
                related["stage"] = "news" if related.get("news") else "consequence"
            else:
                related["stage"] = "consequence"
            state["information_seen_keys"].append(key)
            state["information_seen_keys"] = state["information_seen_keys"][-800:]
            return related
    if key in set(state.get("information_seen_keys") or []):
        # News publication may happen after the original rumour. Enrich the
        # existing thread instead of duplicating the story.
        thread = next((row for row in reversed(state["information_threads"]) if row.get("source_key") == key), None)
        if thread and news_id:
            thread["news"] = {"id": news_id, "headline": headline, "detail": detail, "date": event.get("date")}
            thread["stage"] = "news"
        return thread
    certainty = 55 if kind in RUMOUR_KINDS else 95 if kind in PUBLIC_FACT_KINDS else 80
    thread = {
        "id": f"info-{len(state['information_threads']) + 1}", "source_key": key, "date": str(event.get("date") or state.get("current_date") or ""),
        "origin_kind": kind, "fact": {"kind": kind, "entity": {k: event.get(k) for k in ("player_id", "team_id", "from_team_id", "to_team_id", "buyer_team_id") if event.get(k) is not None}},
        "rumour": None, "news": None, "reactions": [], "consequences": [], "certainty": certainty,
        "stage": "fact",
    }
    if kind in RUMOUR_KINDS:
        thread["rumour"] = {"date": thread["date"], "certainty": certainty, "text": headline or detail or "Hay movimiento real alrededor de esta operación."}
        thread["stage"] = "rumour"
    if news_id:
        thread["news"] = {"id": news_id, "headline": headline, "detail": detail, "date": thread["date"]}
        thread["stage"] = "news"
    state["information_threads"].append(thread)
    state["information_threads"] = state["information_threads"][-500:]
    state["information_seen_keys"].append(key)
    state["information_seen_keys"] = state["information_seen_keys"][-800:]
    return thread


def add_reaction(state: dict[str, Any], *, thread_id: str, actor: str, sentiment: str, text: str, date_text: str, consequence: dict[str, Any] | None = None) -> dict[str, Any]:
    ensure_information_state(state)
    thread = next((row for row in state["information_threads"] if row.get("id") == thread_id), None)
    if thread is None:
        raise KeyError("hilo informativo no encontrado")
    reaction = {"date": date_text, "actor": actor, "sentiment": sentiment, "text": text}
    thread.setdefault("reactions", []).append(reaction)
    if consequence:
        thread.setdefault("consequences", []).append({"date": date_text, **consequence})
        thread["stage"] = "consequence"
    elif thread.get("news"):
        thread["stage"] = "reaction"
    return dict(reaction)


def process_information_day(state: dict[str, Any], *, day: date) -> list[dict[str, Any]]:
    ensure_information_state(state)
    events: list[dict[str, Any]] = []
    for thread in state.get("information_threads") or []:
        if thread.get("rumour") and not thread.get("news"):
            started = date.fromisoformat(str(thread.get("date")))
            if day >= started + timedelta(days=3):
                # A rumour without a confirming event fades; it is not upgraded
                # to truth by the media system itself.
                if thread.get("stage") == "rumour":
                    thread["stage"] = "cooled"
                    thread["certainty"] = max(20, int(thread.get("certainty") or 50) - 20)
                    events.append({"kind": "rumour_cooled", "date": day.isoformat(), "thread_id": thread["id"]})
    return events


def information_snapshot(state: dict[str, Any], *, limit: int = 80) -> dict[str, Any]:
    ensure_information_state(state)
    rows = list(state.get("information_threads") or [])
    rows.sort(key=lambda row: (str(row.get("date") or ""), int(str(row.get("id") or "0").split("-")[-1]) if str(row.get("id") or "").split("-")[-1].isdigit() else 0), reverse=True)
    return {"threads": [dict(row) for row in rows[:max(1, min(200, int(limit))) ]], "media_reputation": dict(state.get("media_reputation") or {})}
