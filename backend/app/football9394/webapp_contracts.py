from __future__ import annotations

from pydantic import BaseModel, Field

class TacticsPayload(BaseModel):
    formation: str = "4-4-2"
    mentality: str = "balanced"
    tempo: str = "normal"
    pressing: str = "medium"
    directness: str = "mixed"
    defensive_line: str = "medium"
    width: str = "normal"
    offside_trap: bool = False
    marking: str = "zonal"
    build_up: str = "balanced"
    final_third: str = "mixed"
    transition: str = "balanced"

class SimulatePayload(BaseModel):
    home_team_id: int | None = None
    away_team_id: int | None = None
    home_name: str = "Racing de Santander"
    away_name: str = "Real Sociedad"
    home_level: int = Field(72, ge=45, le=95)
    away_level: int = Field(76, ge=45, le=95)
    seed: int = 9394
    home_tactics: TacticsPayload = Field(default_factory=TacticsPayload)
    away_tactics: TacticsPayload = Field(default_factory=TacticsPayload)

class WorldSeasonPayload(BaseModel):
    seed: int = 9394

class CreateManagerCareerPayload(BaseModel):
    team_id: int = 16
    league_id: int | None = None
    seed: int = 9394
    through_matchday: int = Field(0, ge=0, le=44)
    age_policy: str = "frozen_attributes_dynamic"

class CareerTacticsPayload(TacticsPayload):
    pass

class CareerSelectionPayload(BaseModel):
    starter_ids: list[int] | None = None
    bench_ids: list[int] | None = None
    auto_select: bool = False

class TransferOfferPayload(BaseModel):
    fee_offer: int = Field(ge=0)
    salary_offer: int = Field(default=0, ge=0)
    contract_years: int = Field(default=3, ge=1, le=6)

class ContractRenewalPayload(BaseModel):
    years: int = Field(default=3, ge=1, le=6)
    salary_offer: int | None = Field(default=None, ge=0)

class LiveStartPayload(BaseModel):
    tactics: CareerTacticsPayload | None = None
    starter_ids: list[int] | None = None
    bench_ids: list[int] | None = None

class LiveAdvancePayload(BaseModel):
    minutes: int = Field(default=5, ge=1, le=45)
    until_event: bool = False

class LiveSubstitutionPayload(BaseModel):
    outgoing_id: int
    incoming_id: int

class MarketNegotiationPayload(BaseModel):
    player_id: int
    fee_offer: int = Field(default=0, ge=0)
    salary_offer: int = Field(default=0, ge=0)
    contract_years: int = Field(default=3, ge=1, le=6)
    squad_role: str = "rotation"
    signing_bonus: int = Field(default=0, ge=0)
    release_clause: int | None = Field(default=None, ge=1)
    deal_type: str = "transfer"
    loan_wage_share: int = Field(default=100, ge=0, le=100)

class MarketCounterPayload(BaseModel):
    fee_offer: int = Field(default=0, ge=0)
    salary_offer: int = Field(default=0, ge=0)
    contract_years: int = Field(default=3, ge=1, le=6)
    loan_wage_share: int | None = Field(default=None, ge=0, le=100)

class WatchlistPayload(BaseModel):
    watched: bool = True

class TransferListingPayload(BaseModel):
    asking_price: int | None = Field(default=None, ge=0)

class RolePromisePayload(BaseModel):
    role: str

class StaffResponsibilityPayload(BaseModel):
    assignee: str

class TrainingPlanPayload(BaseModel):
    intensity: str | None = None
    weekly_plan: list[str] | None = None
    mode: str | None = None

class TrainingFocusPayload(BaseModel):
    focus: str

class TrainingRecoveryPayload(BaseModel):
    recovery: str

class MatchPreparationPayload(BaseModel):
    focus: str

class TacticalPhasePayload(BaseModel):
    build_up: str | None = None
    final_third: str | None = None
    transition: str | None = None

class TacticalPlayerInstructionPayload(BaseModel):
    duty: str = "support"
    freedom: str = "balanced"
    pressing: str = "normal"
    clear: bool = False

class OppositionInstructionPayload(BaseModel):
    tight_mark: bool = False
    press: bool = False
    show_foot: str = "none"

class SetPieceTakerPayload(BaseModel):
    player_id: int | None = None

class DressingConcernPayload(BaseModel):
    response: str

class DisciplinePayload(BaseModel):
    action: str

class NationalSelectionPayload(BaseModel):
    player_ids: list[int]

