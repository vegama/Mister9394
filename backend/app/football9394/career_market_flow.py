from __future__ import annotations

from datetime import date, timedelta
from random import Random
from typing import Any
from uuid import uuid4

from .career_economy import inferred_annual_salary
from .career_market import estimated_transfer_value


def ensure_market_flow_state(state: dict[str, Any]) -> None:
    state.setdefault("watchlist", [])
    state.setdefault("transfer_negotiations", {})
    state.setdefault("transfer_listings", {})
    state.setdefault("incoming_transfer_offers", [])


def market_flags(player: dict[str, Any], *, overall: int, team_id: int, contract: dict[str, Any], current_year: int, wants_move: bool = False, satisfaction: int | None = None) -> dict[str, Any]:
    value = estimated_transfer_value(player, overall=overall)
    free_agent = int(team_id) == 0
    expiring = int(contract.get("end_year") or 9999) <= current_year + 1
    # Transferability must emerge from football circumstances, never from a
    # player-id lottery.  Reserve status is source data; contract pressure and
    # squad dissatisfaction are career state.
    reserve = bool(player.get("initially_reserve"))
    listed_hint = bool(free_agent or expiring or reserve or wants_move)
    return {
        "free_agent": free_agent, "expiring": expiring, "market_value": value,
        "transferable_hint": listed_hint, "wants_move": bool(wants_move),
        "satisfaction": satisfaction,
        "minimum_salary_hint": round(inferred_annual_salary(player, overall=overall) * (.84 if wants_move else .90)),
        "reason": ("quiere_salir" if wants_move else "contrato_corto" if expiring else "reserva" if reserve else None),
    }


def new_negotiation(*, state: dict[str, Any], player_id: int, seller_team_id: int, buyer_team_id: int,
                    fee_offer: int, salary_offer: int, contract_years: int, current_date: date, seed: int, rival_interest: bool = False) -> dict[str, Any]:
    ensure_market_flow_state(state)
    existing = next((row for row in state["transfer_negotiations"].values()
                     if int(row.get("player_id") or 0) == int(player_id) and row.get("status") in {"waiting", "countered"}), None)
    if existing:
        raise ValueError("ya existe una negociación abierta por este futbolista")
    nid = str(uuid4())
    rng = Random(int(seed) ^ int(player_id) * 7919 ^ current_date.toordinal())
    delay = 1 + rng.randint(0, 2)
    rivalry = bool(rival_interest)
    row = {
        "id": nid, "player_id": int(player_id), "seller_team_id": int(seller_team_id), "buyer_team_id": int(buyer_team_id),
        "status": "waiting", "opened_on": current_date.isoformat(), "response_date": (current_date + timedelta(days=delay)).isoformat(),
        "round": 1, "fee_offer": int(fee_offer), "salary_offer": int(salary_offer), "contract_years": int(contract_years),
        "rival_interest": rivalry, "history": [{"date": current_date.isoformat(), "kind": "offer", "fee": int(fee_offer), "salary": int(salary_offer), "years": int(contract_years)}],
    }
    state["transfer_negotiations"][nid] = row
    return row


def resubmit_negotiation(row: dict[str, Any], *, fee_offer: int, salary_offer: int, contract_years: int,
                         current_date: date, seed: int) -> dict[str, Any]:
    if row.get("status") not in {"countered", "rejected"}:
        raise ValueError("la negociación todavía no admite una nueva oferta")
    round_number = int(row.get("round") or 1) + 1
    rng = Random(int(seed) ^ int(row["player_id"]) * 6151 ^ current_date.toordinal() ^ round_number)
    row.update({
        "status": "waiting", "round": round_number, "fee_offer": int(fee_offer), "salary_offer": int(salary_offer),
        "contract_years": int(contract_years), "response_date": (current_date + timedelta(days=1 + rng.randint(0, 1))).isoformat(),
    })
    row.setdefault("history", []).append({"date": current_date.isoformat(), "kind": "offer", "fee": int(fee_offer), "salary": int(salary_offer), "years": int(contract_years)})
    return row
