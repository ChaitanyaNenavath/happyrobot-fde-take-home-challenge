"""Derive authoritative call fields from the HappyRobot transcript.

The platform's Extract/Classify nodes are LLM-based and unreliable (they have been
observed returning empty fields and the wrong outcome). The transcript itself is the
ground truth: it includes every spoken turn AND the JSON results returned by the
verify_carrier and find_available_loads tools. This module reads those to recover the
MC number, the load that was actually pitched, the agreed rate, and the real outcome.
"""
from __future__ import annotations

import json
import re
from typing import Any

from app.services.analysis import classify_sentiment

_BOOKED = (
    "transfer was successful",
    "book this load at the agreed rate",
    "we can book this load",
    "book it at the agreed rate",
)
_NOT_ELIGIBLE = (
    "unable to move forward",
    "carrier verification result",
    "not eligible",
    "verification failed",
)
_NO_LOAD = (
    "couldn't find a matching load",
    "could not find a matching load",
    "couldn't find a load",
    "no matching load",
)
_NEG_FAIL = (
    "not able to meet that rate",
    "we're not able to meet",
    "we are not able to meet",
    "best we can do",
)
_DECLINE = ("not interested", "i'll pass", "i will pass", "no thanks", "we'll pass")


def _first(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", []):
            return value
    return None


def _flatten(transcript: Any) -> tuple[str, list[tuple[Any, dict]], list[tuple[Any, dict]]]:
    """Return (readable_text, tool_results, tool_call_args)."""
    if isinstance(transcript, str):
        return transcript, [], []
    if not isinstance(transcript, list):
        return str(transcript or ""), [], []

    texts: list[str] = []
    results: list[tuple[Any, dict]] = []
    args: list[tuple[Any, dict]] = []

    for message in transcript:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = message.get("content")

        if role == "tool" and isinstance(content, str):
            try:
                results.append((message.get("name"), json.loads(content)))
            except (ValueError, TypeError):
                pass
        elif isinstance(content, str) and content.strip():
            speaker = "Carrier" if role == "user" else "Agent"
            texts.append(f"{speaker}: {content}")

        for call in message.get("tool_calls") or []:
            function = call.get("function", {}) if isinstance(call, dict) else {}
            try:
                args.append((function.get("name"), json.loads(function.get("arguments", "{}"))))
            except (ValueError, TypeError):
                pass

    return "\n".join(texts), results, args


def derive_fields(transcript: Any) -> dict[str, Any]:
    text, results, args = _flatten(transcript)
    low = text.lower()

    mc_number = carrier_name = load_id = None
    carrier_approved = None
    load_rate = None

    for name, data in results:
        if not isinstance(data, dict):
            continue
        if name == "verify_carrier" or "approved" in data:
            if data.get("mc_number"):
                mc_number = _first(mc_number, re.sub(r"\D", "", str(data["mc_number"])) or None)
            carrier_name = _first(carrier_name, data.get("carrier_name"))
            if "approved" in data:
                carrier_approved = bool(data.get("approved"))
        if name == "find_available_loads" or "results" in data or "load_id" in data:
            load = None
            if isinstance(data.get("results"), list) and data["results"]:
                load = data["results"][0]
            elif data.get("load_id"):
                load = data
            if isinstance(load, dict):
                load_id = _first(load_id, load.get("load_id"))
                load_rate = _first(load_rate, load.get("loadboard_rate"))

    for name, data in args:
        if isinstance(data, dict) and data.get("mc_number"):
            digits = re.sub(r"\D", "", str(data["mc_number"]))
            mc_number = _first(mc_number, digits or None)

    if not mc_number:
        match = re.search(r"\bmc\W*(\d{4,8})", low)
        mc_number = match.group(1) if match else None
    if not load_id:
        match = re.search(r"\bLD\s*0*([0-9]{1,5})", text, re.IGNORECASE)
        load_id = f"LD{int(match.group(1)):03d}" if match else None

    outcome = None
    if any(signal in low for signal in _BOOKED):
        outcome = "BOOKED"
    elif carrier_approved is False or any(signal in low for signal in _NOT_ELIGIBLE):
        outcome = "CARRIER_NOT_ELIGIBLE"
    elif any(signal in low for signal in _NEG_FAIL):
        outcome = "NEGOTIATION_FAILED"
    elif any(signal in low for signal in _NO_LOAD):
        outcome = "NO_LOAD_FOUND"
    elif any(signal in low for signal in _DECLINE):
        outcome = "NOT_INTERESTED"

    carrier_offer = None
    offer_keywords = (
        "do it for", "can do it", "can do", "how about", "take it for",
        "give me", "i'll do", "ill do", "my rate", "looking for", "need",
    )
    for line in text.splitlines():
        low_line = line.lower()
        if not low_line.startswith("carrier:"):
            continue
        if "$" not in line and not any(keyword in low_line for keyword in offer_keywords):
            continue
        cleaned = line.replace(",", "")
        amounts = re.findall(r"\$\s?(\d{3,5}(?:\.\d{1,2})?)", cleaned)
        if not amounts:
            amounts = re.findall(r"\b(\d{3,5}(?:\.\d{1,2})?)\b", cleaned)
        amounts = [value for value in amounts if value != mc_number]
        if amounts:
            carrier_offer = float(amounts[-1])

    final_rate = None
    if outcome == "BOOKED":
        final_rate = float(_first(carrier_offer, load_rate) or 0) or None

    return {
        "mc_number": mc_number,
        "carrier_name": carrier_name,
        "carrier_approved": carrier_approved,
        "load_id": load_id,
        "carrier_offer": carrier_offer,
        "final_rate": final_rate,
        "outcome": outcome,
        "sentiment": classify_sentiment(text).value if text else None,
        "transcript_text": text,
    }


def enrich_record_from_transcript(payload: dict[str, Any]) -> dict[str, Any]:
    """Fill empty/missing fields and correct the outcome using the transcript.

    The transcript is treated as ground truth: a derived outcome (e.g. BOOKED detected
    from "transfer was successful") overrides whatever the Classify node reported.
    """
    record = dict(payload or {})
    derived = derive_fields(record.get("transcript"))

    def is_empty(value: Any) -> bool:
        return value in (None, "", [], {})

    if derived["outcome"]:
        record["outcome"] = derived["outcome"]

    for field in ("mc_number", "carrier_name", "load_id", "carrier_offer", "final_rate"):
        if is_empty(record.get(field)) and not is_empty(derived.get(field)):
            record[field] = derived[field]

    if is_empty(record.get("sentiment")) and derived.get("sentiment"):
        record["sentiment"] = derived["sentiment"]
    if is_empty(record.get("carrier_approved")) and derived.get("carrier_approved") is not None:
        record["carrier_approved"] = derived["carrier_approved"]

    record["transcript"] = derived["transcript_text"] or (
        record["transcript"] if isinstance(record.get("transcript"), str) else ""
    )
    record.setdefault("data_source", "happyrobot")
    return record
