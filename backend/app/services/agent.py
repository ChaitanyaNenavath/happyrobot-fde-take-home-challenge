from __future__ import annotations

import re
from typing import Any

from app.database import save_call_record
from app.models import CarrierSentiment, CallOutcome
from app.services.analysis import classify_sentiment, extract_relevant_call_data
from app.services.fmcsa import verify_carrier
from app.services.loads import format_load_pitch, get_load_by_id, load_catalog, search_loads
from app.services.negotiation import negotiate_offers
from app.services.session_store import create_session, get_session, save_session

CATALOG_LOADS = load_catalog()
CITY_HINTS = sorted(
    {
        load[field].split(",")[0].strip().lower()
        for load in CATALOG_LOADS
        for field in ("origin", "destination")
    }
)
EQUIPMENT_HINTS = sorted({load["equipment_type"].lower() for load in CATALOG_LOADS})
LOAD_ID_HINTS = sorted({load["load_id"] for load in CATALOG_LOADS})


def start_agent_session() -> dict[str, Any]:

    session = create_session()
    return {
        "session_id": session["session_id"],
        "stage": session["stage"],
        "response": (
            "Thanks for calling about available freight. "
            "Please share your MC number so I can verify your authority."
        ),
    }


def handle_agent_turn(session_id: str, utterance: str) -> dict[str, Any]:

    session = get_session(session_id)

    if not session:
        return {
            "error": "Session not found.",
            "response": "I could not find that call session. Please start a new call.",
        }

    if session["closed"]:
        return {
            "session_id": session_id,
            "stage": "closed",
            "response": "This call is already complete.",
            "result": session["result"],
        }

    _append_turn(session, "carrier", utterance)
    stage = session["stage"]

    if stage == "collect_mc_number":
        return _handle_mc_collection(session, utterance)

    if stage in {"collect_origin", "collect_destination", "collect_equipment"}:
        return _handle_load_preferences(session, utterance)

    if stage == "pitch_load":
        return _handle_pitch_response(session, utterance)

    if stage == "negotiate":
        return _handle_negotiation(session, utterance)

    return _close_session(
        session,
        response="The workflow reached an unsupported state. Please restart the call.",
        outcome=CallOutcome.NEGOTIATION_FAILED,
    )


def _handle_mc_collection(session: dict[str, Any], utterance: str) -> dict[str, Any]:

    mc_number = _extract_mc_number(utterance)

    if not mc_number:
        if _is_demo_number_request(utterance):
            return _reply(
                session,
                response=(
                    "For this demo, enter any 6 digit MC number such as 123456 or 198982. "
                    "Numbers ending in 0 or 5 are treated as blocked in mock mode."
                ),
            )

        return _reply(
            session,
            response="I still need your MC number to continue. Please provide the MC number.",
        )

    carrier = verify_carrier(mc_number)
    session["mc_number"] = mc_number
    session["carrier"] = carrier

    if not carrier["approved"]:
        response = (
            "I am not able to confirm active operating authority for that MC number, "
            "so I cannot release a load today."
        )
        return _close_session(
            session,
            response=response,
            outcome=CallOutcome.CARRIER_NOT_ELIGIBLE,
        )

    session["stage"] = "collect_origin"
    save_session(session)

    return _reply(
        session,
        response=(
            f"Thanks. MC {mc_number} is approved and ready to book. "
            "If you already have a load ID, share it now. Otherwise, what origin city are you covering?"
        ),
    )


def _handle_load_preferences(session: dict[str, Any], utterance: str) -> dict[str, Any]:

    stage = session["stage"]
    preferences = _extract_load_preferences(utterance)
    preferences = _normalize_preferences_for_stage(stage, preferences, utterance)

    clarification_message = _build_preference_clarification(stage, utterance, preferences)
    if clarification_message:
        return _reply(
            session,
            response=clarification_message,
        )

    guidance_message = _build_stage_guidance(session, stage, utterance, preferences)
    if guidance_message:
        return _reply(
            session,
            response=guidance_message,
        )

    session["load_preferences"].update(
        {
            key: preferences.get(key)
            for key in ("load_id", "origin", "destination", "equipment_type")
            if preferences.get(key)
        }
    )

    selected_load = None

    if preferences.get("load_id"):
        selected_load = get_load_by_id(preferences["load_id"])

    if not selected_load:
        missing_field = _next_missing_load_field(session["load_preferences"])

        if missing_field:
            session["stage"] = missing_field
            save_session(session)
            return _reply(
                session,
                response=_question_for_stage(missing_field, session),
            )

    if not selected_load:
        loads = search_loads(
            origin=session["load_preferences"].get("origin"),
            destination=session["load_preferences"].get("destination"),
            equipment_type=session["load_preferences"].get("equipment_type"),
            max_results=3,
        )
        session["load_options"] = loads
        selected_load = loads[0] if loads else None

    if not selected_load:
        alternative_message = _build_no_match_response(session)
        if alternative_message:
            return _reply(
                session,
                response=alternative_message,
            )

        return _close_session(
            session,
            response=(
                "I do not have a viable load match for that lane and equipment right now."
            ),
            outcome=CallOutcome.NO_LOAD_FOUND,
        )

    session["selected_load"] = selected_load
    session["stage"] = "pitch_load"
    save_session(session)

    return _reply(
        session,
        response=(
            f"{format_load_pitch(selected_load)} "
            "Are you interested in taking this load at the posted rate?"
        ),
        extra={"matched_load": selected_load},
    )


def _handle_pitch_response(session: dict[str, Any], utterance: str) -> dict[str, Any]:

    normalized = utterance.lower()

    if any(token in normalized for token in ["yes", "sounds good", "works", "book it", "take it"]):
        return _close_session(
            session,
            response="Transfer was successful and now you can wrap up the conversation.",
            outcome=CallOutcome.BOOKED,
            final_rate=session["selected_load"]["loadboard_rate"],
        )

    if any(token in normalized for token in ["no", "pass", "not interested", "decline"]):
        return _close_session(
            session,
            response="Understood. I will mark this load as declined. Thanks for calling.",
            outcome=CallOutcome.NOT_INTERESTED,
        )

    offers = _extract_offers(utterance)

    if not offers:
        return _reply(
            session,
            response=(
                "If you want to negotiate, please tell me your rate. "
                "Otherwise confirm whether you want the posted rate."
            ),
        )

    session["offers"].extend(offers[: 3 - len(session["offers"])])
    session["stage"] = "negotiate"
    save_session(session)
    return _handle_negotiation(session, utterance)


def _handle_negotiation(session: dict[str, Any], utterance: str) -> dict[str, Any]:

    new_offers = _extract_offers(utterance)

    for offer in new_offers:
        if len(session["offers"]) < 3:
            session["offers"].append(offer)

    result = negotiate_offers(
        session["selected_load"]["loadboard_rate"],
        session["offers"],
    )
    save_session(session)

    if result["accepted"]:
        return _close_session(
            session,
            response=result["transfer_message"],
            outcome=CallOutcome.BOOKED,
            final_rate=result["final_rate"],
            counter_offer=result["counter_offer"],
            negotiation_rounds=result["negotiation_rounds"],
        )

    if len(session["offers"]) >= 3:
        return _close_session(
            session,
            response=(
                f"{result['message']} We are not able to go higher, so I will close this out here."
            ),
            outcome=CallOutcome.NEGOTIATION_FAILED,
            counter_offer=result["counter_offer"],
            negotiation_rounds=result["negotiation_rounds"],
        )

    return _reply(
        session,
        response=(
            f"{result['message']} If you want to continue, give me your next best offer."
        ),
        extra={"negotiation": result},
    )


def _close_session(
    session: dict[str, Any],
    *,
    response: str,
    outcome: CallOutcome,
    final_rate: float = 0,
    counter_offer: float | None = None,
    negotiation_rounds: int | None = None,
) -> dict[str, Any]:

    _append_turn(session, "assistant", response)
    transcript = _join_transcript(session["transcript_turns"])
    sentiment = classify_sentiment(transcript)
    extracted = extract_relevant_call_data(transcript, session["offers"])
    selected_load = session.get("selected_load")
    result = negotiate_offers(
        selected_load["loadboard_rate"],
        session["offers"],
    ) if selected_load else {
        "history": [],
        "counter_offer": counter_offer,
        "negotiation_rounds": negotiation_rounds or len(session["offers"]),
    }

    record = {
        "mc_number": session.get("mc_number"),
        "load_id": selected_load["load_id"] if selected_load else None,
        "outcome": outcome.value,
        "sentiment": sentiment.value if isinstance(sentiment, CarrierSentiment) else sentiment,
        "final_rate": final_rate,
        "carrier_approved": bool(session.get("carrier", {}).get("approved")),
        "carrier_offer": session["offers"][-1] if session["offers"] else None,
        "counter_offer": counter_offer if counter_offer is not None else result.get("counter_offer"),
        "negotiation_rounds": negotiation_rounds if negotiation_rounds is not None else result.get("negotiation_rounds", len(session["offers"])),
        "summary": _build_summary(session, outcome, final_rate),
        "transcript": transcript,
        "carrier_name": session.get("carrier_name") or session.get("carrier", {}).get("carrier_name"),
        "data_source": "agent_workflow",
        "extracted_data": {
            **extracted,
            "verification": session.get("carrier"),
            "negotiation_history": result.get("history", []),
            "load_preferences": session.get("load_preferences", {}),
        },
    }
    record_id = save_call_record(record)

    session["closed"] = True
    session["stage"] = "closed"
    session["result"] = {
        "record_id": record_id,
        "outcome": outcome.value,
        "sentiment": sentiment.value if isinstance(sentiment, CarrierSentiment) else sentiment,
        "final_rate": final_rate,
        "matched_load": selected_load,
    }
    save_session(session)

    return {
        "session_id": session["session_id"],
        "stage": session["stage"],
        "response": response,
        "result": session["result"],
    }


def _reply(
    session: dict[str, Any],
    *,
    response: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:

    _append_turn(session, "assistant", response)
    save_session(session)

    payload = {
        "session_id": session["session_id"],
        "stage": session["stage"],
        "response": response,
    }

    if extra:
        payload.update(extra)

    return payload


def _append_turn(session: dict[str, Any], speaker: str, text: str) -> None:

    session["transcript_turns"].append({"speaker": speaker, "text": text})


def _join_transcript(turns: list[dict[str, str]]) -> str:

    return "\n".join(f"{turn['speaker']}: {turn['text']}" for turn in turns)


def _extract_mc_number(text: str) -> str | None:

    match = re.search(r"(?:mc\s*)?(\d{4,10})", text, flags=re.IGNORECASE)
    return match.group(1) if match else None


def _is_demo_number_request(text: str) -> bool:

    lowered = text.lower()
    trigger_phrases = (
        "new number",
        "new mc",
        "new mc number",
        "demo number",
        "generate number",
        "give me a number",
        "need a number",
        "create number",
    )
    return any(phrase in lowered for phrase in trigger_phrases)


def _extract_offers(text: str) -> list[float]:

    matches = re.findall(r"\$?\s?(\d{3,5}(?:\.\d{1,2})?)", text)
    return [float(match) for match in matches]


def _extract_load_preferences(text: str) -> dict[str, Any]:

    lowered = text.lower()
    load_id_match = re.search(r"\bld\d{3}\b", text, flags=re.IGNORECASE)
    equipment = next((item for item in EQUIPMENT_HINTS if item in lowered), None)
    explicit_origin = _extract_labeled_location(text, ("origin", "from"))
    explicit_destination = _extract_labeled_location(text, ("destination", "dest", "to"))

    mentioned_cities = [city.title() for city in CITY_HINTS if city in lowered]
    origin = explicit_origin or (mentioned_cities[0] if len(mentioned_cities) >= 1 else None)
    destination = explicit_destination or (mentioned_cities[1] if len(mentioned_cities) >= 2 else None)

    if "to " in lowered:
        to_fragment = lowered.split("to ", 1)[1]
        for city in CITY_HINTS:
            if city in to_fragment:
                destination = city.title()
                break

    return {
        "load_id": load_id_match.group(0).upper() if load_id_match else None,
        "origin": origin,
        "destination": destination,
        "equipment_type": equipment.title() if equipment else None,
        "mentioned_load_id": _extract_requested_load_id_token(text),
    }


def _normalize_preferences_for_stage(
    stage: str,
    preferences: dict[str, Any],
    text: str,
) -> dict[str, Any]:

    city = _extract_single_city(text)

    if stage == "collect_origin" and city and not preferences.get("origin"):
        preferences["origin"] = city

    if stage == "collect_destination" and city:
        preferences["destination"] = city
        if preferences.get("origin") == city:
            preferences["origin"] = None

    if stage == "collect_equipment" and not preferences.get("equipment_type"):
        lowered = text.lower()
        if "van" in lowered:
            preferences["equipment_type"] = "Dry Van"
        elif "reefer" in lowered:
            preferences["equipment_type"] = "Reefer"
        elif "flatbed" in lowered:
            preferences["equipment_type"] = "Flatbed"
        elif "power only" in lowered:
            preferences["equipment_type"] = "Power Only"

    return preferences


def _build_preference_clarification(
    stage: str,
    text: str,
    preferences: dict[str, Any],
) -> str | None:

    messages: list[str] = []
    mentioned_load_id = preferences.get("mentioned_load_id")
    lowered = text.lower()

    if mentioned_load_id and not preferences.get("load_id"):
        messages.append(
            "I could not recognize that load ID. Use a demo load ID like LD001, or give me the lane details."
        )

    if _mentions_labeled_field(lowered, ("destination", "dest")) and not preferences.get("destination"):
        messages.append(
            f"I could not recognize that destination city. Try one of the demo cities: {_format_choice_list(_available_destinations())}."
        )

    if _mentions_labeled_field(lowered, ("origin", "from")) and not preferences.get("origin"):
        messages.append(
            f"I could not recognize that origin city. Try one of the demo cities: {_format_choice_list(_available_origins())}."
        )

    if _mentions_labeled_field(lowered, ("equipment", "truck", "trailer")) and not preferences.get("equipment_type"):
        messages.append(
            f"I could not recognize that equipment type. Use {_format_choice_list(_available_equipment_types())}."
        )

    if not messages:
        return None

    if stage == "collect_origin" and not preferences.get("load_id"):
        messages.append("What origin city are you covering?")
    elif stage == "collect_destination":
        messages.append("What destination city do you want to deliver into?")
    elif stage == "collect_equipment":
        messages.append("What equipment type do you need for this load?")

    return " ".join(messages)


def _extract_single_city(text: str) -> str | None:

    lowered = text.lower()

    for city in CITY_HINTS:
        if city in lowered:
            return city.title()

    return None


def _next_missing_load_field(preferences: dict[str, Any]) -> str | None:

    if not preferences.get("origin"):
        return "collect_origin"

    if not preferences.get("destination"):
        return "collect_destination"

    if not preferences.get("equipment_type"):
        return "collect_equipment"

    return None


def _question_for_stage(stage: str, session: dict[str, Any] | None = None) -> str:

    if stage == "collect_origin":
        return (
            f"What origin city are you covering? Available origins are {_format_choice_list(_available_origins())}. "
            f"You can also give me a load ID like {_format_choice_list(LOAD_ID_HINTS)}."
        )

    if stage == "collect_destination":
        return (
            "What destination city do you want to deliver into? "
            f"Available destinations are {_format_choice_list(_available_destinations(session))}."
        )

    return (
        "What equipment type do you need for this load? "
        f"Available equipment types are {_format_choice_list(_available_equipment_types(session))}."
    )


def _build_summary(
    session: dict[str, Any],
    outcome: CallOutcome,
    final_rate: float,
) -> str:

    carrier = session.get("carrier", {})
    selected_load = session.get("selected_load")
    load_fragment = (
        f"Matched to {selected_load['load_id']} at ${final_rate:.2f}."
        if selected_load and final_rate
        else "No final booked rate."
    )
    return (
        f"Carrier MC {session.get('mc_number')} "
        f"verification={carrier.get('approved', False)} "
        f"outcome={outcome.value}. {load_fragment}"
    )


def _extract_requested_load_id_token(text: str) -> str | None:

    match = re.search(
        r"\b(?:load\s*id|id)\s*(?:is|=)?\s*([a-z0-9-]+)\b",
        text,
        flags=re.IGNORECASE,
    )
    return match.group(1).upper() if match else None


def _extract_labeled_location(text: str, labels: tuple[str, ...]) -> str | None:

    for label in labels:
        match = re.search(
            rf"\b{label}\b\s*(?:is|=)?\s*([a-z ]+?)(?=\s+\b(?:and|with|for|equipment|load|id|mc|destination|origin|from|to)\b|$)",
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            continue

        candidate = match.group(1).strip().lower()
        for city in CITY_HINTS:
            if city == candidate or city in candidate:
                return city.title()

    return None


def _mentions_labeled_field(text: str, labels: tuple[str, ...]) -> bool:

    return any(re.search(rf"\b{label}\b", text, flags=re.IGNORECASE) for label in labels)


def _build_stage_guidance(
    session: dict[str, Any],
    stage: str,
    text: str,
    preferences: dict[str, Any],
) -> str | None:

    if _is_options_request(text):
        return _build_options_response(session, stage)

    if stage == "collect_origin" and not preferences.get("origin") and not preferences.get("load_id"):
        candidate = _extract_free_text_candidate(text)
        if candidate:
            return (
                f"I do not have {candidate.title()} in the current demo lanes. "
                f"Available origin cities are {_format_choice_list(_available_origins())}. "
                f"You can also use load IDs {_format_choice_list(LOAD_ID_HINTS)}."
            )

    if stage == "collect_destination" and not preferences.get("destination"):
        candidate = _extract_free_text_candidate(text)
        if candidate:
            return (
                f"I do not have {candidate.title()} as a destination for this demo flow. "
                f"Available destination cities are {_format_choice_list(_available_destinations(session))}."
            )

    if stage == "collect_equipment" and not preferences.get("equipment_type"):
        candidate = _extract_free_text_candidate(text)
        if candidate:
            return (
                f"I do not have {candidate.title()} as an equipment option here. "
                f"Available equipment types are {_format_choice_list(_available_equipment_types(session))}."
            )

    return None


def _build_options_response(session: dict[str, Any], stage: str) -> str:

    if stage == "collect_origin":
        return (
            f"Current load IDs are {_format_choice_list(LOAD_ID_HINTS)}. "
            f"Available origin cities are {_format_choice_list(_available_origins())}."
        )

    if stage == "collect_destination":
        return (
            f"For this search, available destination cities are {_format_choice_list(_available_destinations(session))}."
        )

    return (
        f"For this lane, available equipment types are {_format_choice_list(_available_equipment_types(session))}."
    )


def _build_no_match_response(session: dict[str, Any]) -> str | None:

    preferences = session.get("load_preferences", {})
    origin = preferences.get("origin")
    destination = preferences.get("destination")
    equipment_type = preferences.get("equipment_type")

    same_lane_loads = search_loads(
        origin=origin,
        destination=destination,
        max_results=10,
    )

    if same_lane_loads and equipment_type:
        available_equipment = sorted({load["equipment_type"] for load in same_lane_loads})
        session["stage"] = "collect_equipment"
        save_session(session)
        return (
            f"I do not have {equipment_type} on that lane. "
            f"For {origin} to {destination}, I currently have {_format_choice_list(available_equipment)}. "
            "Do you want one of those equipment options?"
        )

    same_origin_loads = search_loads(
        origin=origin,
        max_results=10,
    )
    if same_origin_loads and destination:
        available_destinations = sorted(
            {load["destination"].split(",")[0].strip() for load in same_origin_loads}
        )
        session["stage"] = "collect_destination"
        save_session(session)
        return (
            f"I do not have {destination} from {origin}. "
            f"Available destinations from {origin} are {_format_choice_list(available_destinations)}."
        )

    return None


def _available_origins() -> list[str]:

    return sorted({load["origin"].split(",")[0].strip() for load in CATALOG_LOADS})


def _available_destinations(session: dict[str, Any] | None = None) -> list[str]:

    loads = _filter_catalog_loads(session)
    return sorted({load["destination"].split(",")[0].strip() for load in loads}) or sorted(
        {load["destination"].split(",")[0].strip() for load in CATALOG_LOADS}
    )


def _available_equipment_types(session: dict[str, Any] | None = None) -> list[str]:

    loads = _filter_catalog_loads(session)
    return sorted({load["equipment_type"] for load in loads}) or sorted(
        {load["equipment_type"] for load in CATALOG_LOADS}
    )


def _filter_catalog_loads(session: dict[str, Any] | None = None) -> list[dict[str, Any]]:

    if not session:
        return CATALOG_LOADS

    preferences = session.get("load_preferences", {})
    origin = preferences.get("origin")
    destination = preferences.get("destination")
    loads = CATALOG_LOADS

    if origin:
        loads = [load for load in loads if origin.lower() in load["origin"].lower()]

    if destination:
        loads = [load for load in loads if destination.lower() in load["destination"].lower()]

    return loads


def _format_choice_list(values: list[str]) -> str:

    if not values:
        return "no current options"

    if len(values) == 1:
        return values[0]

    if len(values) == 2:
        return f"{values[0]} or {values[1]}"

    return f"{', '.join(values[:-1])}, or {values[-1]}"


def _is_options_request(text: str) -> bool:

    lowered = text.lower()
    trigger_phrases = (
        "options",
        "what are the options",
        "available loads",
        "available cities",
        "what do you have",
        "show loads",
        "list loads",
        "help",
    )
    return any(phrase in lowered for phrase in trigger_phrases)


def _extract_free_text_candidate(text: str) -> str | None:

    lowered = text.lower().strip()
    if not lowered or re.search(r"\d", lowered):
        return None

    if _is_options_request(lowered):
        return None

    cleaned = re.sub(r"[^a-z\s]", " ", lowered)
    words = [word for word in cleaned.split() if word not in {"i", "am", "need", "want", "going", "to", "from", "origin", "destination", "city", "covering"}]
    if not words:
        return None

    return " ".join(words[:3])
