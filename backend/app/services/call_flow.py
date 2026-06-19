from __future__ import annotations

from typing import Any

from app.database import save_call_record
from app.models import CallProcessRequest
from app.services.analysis import (
    classify_sentiment,
    determine_outcome,
    extract_relevant_call_data,
)
from app.services.fmcsa import verify_carrier
from app.services.loads import format_load_pitch, get_load_by_id, search_loads
from app.services.negotiation import negotiate_offers


def process_inbound_call(request: CallProcessRequest) -> dict[str, Any]:

    carrier_status = verify_carrier(request.mc_number)
    call_analysis = extract_relevant_call_data(
        request.transcript,
        request.offers,
    )

    matched_load = None

    if request.load_id:
        matched_load = get_load_by_id(request.load_id)

    if not matched_load:
        potential_loads = search_loads(
            origin=request.origin,
            destination=request.destination,
            equipment_type=request.equipment_type
            or call_analysis.get("requested_equipment"),
            max_results=1,
        )
        matched_load = potential_loads[0] if potential_loads else None

    negotiation_result = {
        "accepted": False,
        "final_rate": 0,
        "counter_offer": None,
        "negotiation_rounds": 0,
        "history": [],
        "message": "No negotiation performed.",
        "transfer_message": None,
    }

    if matched_load and carrier_status["approved"]:
        negotiation_result = negotiate_offers(
            matched_load["loadboard_rate"],
            request.offers or call_analysis["mentioned_offers"],
        )

    sentiment = classify_sentiment(request.transcript)
    outcome = determine_outcome(
        carrier_approved=carrier_status["approved"],
        matched_load=matched_load is not None,
        negotiation_accepted=negotiation_result["accepted"],
        carrier_interested=call_analysis["carrier_interested"],
    )

    final_rate = (
        negotiation_result["final_rate"]
        if negotiation_result["accepted"]
        else 0
    )

    summary_parts = [
        f"Carrier MC {request.mc_number}",
        carrier_status["reason"],
    ]

    if matched_load:
        summary_parts.append(
            f"Matched to load {matched_load['load_id']} at posted rate "
            f"${matched_load['loadboard_rate']:.2f}."
        )
        summary_parts.append(negotiation_result["message"])
    else:
        summary_parts.append("No viable load was matched.")

    summary = " ".join(summary_parts)

    record = {
        "mc_number": request.mc_number,
        "load_id": matched_load["load_id"] if matched_load else request.load_id,
        "outcome": outcome.value,
        "sentiment": sentiment.value,
        "final_rate": final_rate,
        "carrier_approved": carrier_status["approved"],
        "carrier_offer": call_analysis["latest_offer"],
        "counter_offer": negotiation_result["counter_offer"],
        "negotiation_rounds": negotiation_result["negotiation_rounds"],
        "transcript": request.transcript,
        "summary": summary,
        "carrier_name": request.carrier_name or carrier_status.get("carrier_name"),
        "data_source": carrier_status.get("data_source", "workflow"),
        "extracted_data": {
            **call_analysis,
            "verification": carrier_status,
            "negotiation_history": negotiation_result["history"],
        },
    }

    record_id = save_call_record(record)

    return {
        "record_id": record_id,
        "carrier": carrier_status,
        "matched_load": matched_load,
        "load_pitch": format_load_pitch(matched_load) if matched_load else None,
        "negotiation": negotiation_result,
        "outcome": outcome.value,
        "sentiment": sentiment.value,
        "summary": summary,
        "transfer_message": negotiation_result["transfer_message"],
        "extracted_data": record["extracted_data"],
    }
