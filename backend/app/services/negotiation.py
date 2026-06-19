from __future__ import annotations

from typing import Any

from app.config import NEGOTIATION_MARGIN, NEGOTIATION_MAX_ROUNDS


def negotiate(load_rate: float, carrier_offer: float) -> dict[str, Any]:

    return negotiate_offers(load_rate, [carrier_offer])


def negotiate_offers(
    load_rate: float,
    offers: list[float] | None,
    max_rounds: int = NEGOTIATION_MAX_ROUNDS,
) -> dict[str, Any]:

    capped_offers = (offers or [])[:max_rounds]
    max_rate = round(load_rate * (1 + NEGOTIATION_MARGIN), 2)
    history: list[dict[str, Any]] = []

    if not capped_offers:
        return {
            "accepted": True,
            "final_rate": round(load_rate, 2),
            "counter_offer": None,
            "negotiation_rounds": 0,
            "history": history,
            "message": "Carrier accepted the posted rate.",
            "transfer_message": (
                "Transfer was successful and now you can wrap up the conversation."
            ),
        }

    for round_number, offer in enumerate(capped_offers, start=1):
        accepted = offer <= max_rate
        history.append(
            {
                "round": round_number,
                "carrier_offer": round(offer, 2),
                "broker_response": "ACCEPTED" if accepted else "COUNTERED",
                "counter_offer": None if accepted else max_rate,
            }
        )

        if accepted:
            return {
                "accepted": True,
                "final_rate": round(offer, 2),
                "counter_offer": None,
                "negotiation_rounds": round_number,
                "history": history,
                "message": "Offer accepted.",
                "transfer_message": (
                    "Transfer was successful and now you can wrap up the conversation."
                ),
            }

    return {
        "accepted": False,
        "final_rate": None,
        "counter_offer": max_rate,
        "negotiation_rounds": len(capped_offers),
        "history": history,
        "message": f"Best we can do is {max_rate}.",
        "transfer_message": None,
    }
