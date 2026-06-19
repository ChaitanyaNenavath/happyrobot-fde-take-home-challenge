import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

_EMPTY_TOKENS = {"", "null", "none", "n/a", "na", "unknown", "undefined", "-"}


def _to_number(value: Any) -> float | None:
    """Coerce messy voice-extracted values to a number, or None if not present."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("$", "").replace(",", "")
    if text.lower() in _EMPTY_TOKENS:
        return Nones
    try:
        return float(text)
    except ValueError:
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        return float(match.group()) if match else None


def _normalize_label(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in _EMPTY_TOKENS:
        return None
    return text.upper().replace(" ", "_").replace("-", "_")


class CallOutcome(str, Enum):
    BOOKED = "BOOKED"
    NEGOTIATION_FAILED = "NEGOTIATION_FAILED"
    NOT_INTERESTED = "NOT_INTERESTED"
    CARRIER_NOT_ELIGIBLE = "CARRIER_NOT_ELIGIBLE"
    NO_LOAD_FOUND = "NO_LOAD_FOUND"


class CarrierSentiment(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class CarrierRequest(BaseModel):
    mc_number: str = Field(min_length=1)

    @field_validator("mc_number", mode="before")
    @classmethod
    def _coerce_mc(cls, value: Any) -> str:
        return str(value).strip() if value is not None else value


class LoadSearchRequest(BaseModel):
    origin: str | None = None
    destination: str | None = None
    equipment_type: str | None = None
    max_results: int = Field(default=3, ge=1, le=10)


class NegotiationRequest(BaseModel):
    load_id: str
    offers: list[float] = Field(default_factory=list)


class CallRecord(BaseModel):
    mc_number: str = "UNKNOWN"
    load_id: str | None = None
    outcome: CallOutcome
    sentiment: CarrierSentiment = CarrierSentiment.NEUTRAL
    final_rate: float = Field(default=0, ge=0)
    carrier_approved: bool = False
    carrier_offer: float | None = Field(default=None, ge=0)
    counter_offer: float | None = Field(default=None, ge=0)
    negotiation_rounds: int = Field(default=0, ge=0, le=3)
    transcript: str = ""
    carrier_name: str | None = None
    data_source: str = "manual"

    @field_validator("mc_number", mode="before")
    @classmethod
    def _coerce_mc_number(cls, value: Any) -> str:
        if value is None:
            return "UNKNOWN"
        text = str(value).strip()
        return text or "UNKNOWN"

    @field_validator("transcript", mode="before")
    @classmethod
    def _coerce_transcript(cls, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return str(value)

    @field_validator("final_rate", mode="before")
    @classmethod
    def _coerce_final_rate(cls, value: Any) -> float:
        number = _to_number(value)
        return number if number is not None else 0.0

    @field_validator("carrier_offer", "counter_offer", mode="before")
    @classmethod
    def _coerce_optional_money(cls, value: Any) -> float | None:
        return _to_number(value)

    @field_validator("negotiation_rounds", mode="before")
    @classmethod
    def _coerce_rounds(cls, value: Any) -> int:
        number = _to_number(value)
        if number is None:
            return 0
        return max(0, min(3, int(number)))

    @field_validator("outcome", mode="before")
    @classmethod
    def _coerce_outcome(cls, value: Any) -> Any:
        label = _normalize_label(value)
        if label is None:
            return value
        synonyms = {
            "INELIGIBLE": "CARRIER_NOT_ELIGIBLE",
            "NOT_ELIGIBLE": "CARRIER_NOT_ELIGIBLE",
            "DECLINED": "NOT_INTERESTED",
            "CARRIER_DECLINED": "NOT_INTERESTED",
            "NO_MATCHING_LOAD": "NO_LOAD_FOUND",
            "NO_LOAD": "NO_LOAD_FOUND",
        }
        return synonyms.get(label, label)

    @field_validator("sentiment", mode="before")
    @classmethod
    def _coerce_sentiment(cls, value: Any) -> Any:
        label = _normalize_label(value)
        if label is None:
            return CarrierSentiment.NEUTRAL
        if label in {"POSITIVE", "POS", "HAPPY", "GOOD"}:
            return "POSITIVE"
        if label in {"NEGATIVE", "NEG", "ANGRY", "UPSET", "BAD"}:
            return "NEGATIVE"
        if label in {"NEUTRAL", "MIXED", "OKAY", "OK"}:
            return "NEUTRAL"
        return label


class CallProcessRequest(BaseModel):
    mc_number: str = Field(min_length=1)
    load_id: str | None = None
    origin: str | None = None
    destination: str | None = None
    equipment_type: str | None = None
    transcript: str = ""
    offers: list[float] = Field(default_factory=list)
    carrier_name: str | None = None


class AgentTurnRequest(BaseModel):
    session_id: str
    utterance: str = Field(min_length=1)
