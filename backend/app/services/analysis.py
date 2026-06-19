from __future__ import annotations

import re
from typing import Any

from app.models import CallOutcome, CarrierSentiment

POSITIVE_TERMS = {
    "good",
    "great",
    "perfect",
    "works",
    "deal",
    "book",
    "accept",
    "fair",
    "thanks",
}
NEGATIVE_TERMS = {
    "bad",
    "low",
    "can't",
    "cannot",
    "won't",
    "decline",
    "reject",
    "frustrated",
    "upset",
    "expensive",
}
DECLINE_TERMS = {
    "pass",
    "decline",
    "not interested",
    "won't take it",
    "cannot do it",
}
EQUIPMENT_TERMS = ("dry van", "reefer", "flatbed", "power only")


def extract_relevant_call_data(
    transcript: str,
    offers: list[float] | None = None,
) -> dict[str, Any]:

    normalized_transcript = transcript.lower()
    amount_matches = re.findall(r"\$?\s?(\d{3,5}(?:\.\d{1,2})?)", transcript)
    transcript_offers = [float(value) for value in amount_matches]
    combined_offers = list(offers or [])

    for offer in transcript_offers:
        if offer not in combined_offers:
            combined_offers.append(offer)

    requested_equipment = next(
        (
            equipment
            for equipment in EQUIPMENT_TERMS
            if equipment in normalized_transcript
        ),
        None,
    )

    special_requirements = [
        label
        for label, token in (
            ("temperature_control", "temp"),
            ("hazmat", "hazmat"),
            ("liftgate", "liftgate"),
            ("expedite", "urgent"),
            ("expedite", "asap"),
        )
        if token in normalized_transcript
    ]

    return {
        "mentioned_offers": combined_offers[:3],
        "latest_offer": combined_offers[-1] if combined_offers else None,
        "requested_equipment": requested_equipment,
        "special_requirements": special_requirements,
        "carrier_interested": not any(
            phrase in normalized_transcript
            for phrase in DECLINE_TERMS
        ),
    }


def classify_sentiment(transcript: str) -> CarrierSentiment:

    normalized_transcript = transcript.lower()
    positive_hits = sum(
        1 for token in POSITIVE_TERMS if token in normalized_transcript
    )
    negative_hits = sum(
        1 for token in NEGATIVE_TERMS if token in normalized_transcript
    )

    if negative_hits > positive_hits:
        return CarrierSentiment.NEGATIVE

    if positive_hits > negative_hits:
        return CarrierSentiment.POSITIVE

    return CarrierSentiment.NEUTRAL


def determine_outcome(
    *,
    carrier_approved: bool,
    matched_load: bool,
    negotiation_accepted: bool,
    carrier_interested: bool,
) -> CallOutcome:

    if not carrier_approved:
        return CallOutcome.CARRIER_NOT_ELIGIBLE

    if not matched_load:
        return CallOutcome.NO_LOAD_FOUND

    if negotiation_accepted:
        return CallOutcome.BOOKED

    if not carrier_interested:
        return CallOutcome.NOT_INTERESTED

    return CallOutcome.NEGOTIATION_FAILED
