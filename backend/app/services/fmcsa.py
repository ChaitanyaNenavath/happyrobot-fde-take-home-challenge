from __future__ import annotations

from typing import Any

import requests

from app.config import FMCSA_API_KEY, FMCSA_MOCK_MODE, REQUEST_TIMEOUT_SECONDS


def verify_carrier(mc_number: str) -> dict[str, Any]:

    normalized_mc = "".join(ch for ch in mc_number if ch.isdigit()) or mc_number

    if FMCSA_MOCK_MODE or not FMCSA_API_KEY:
        return _mock_verification(normalized_mc)

    try:
        url = (
            "https://mobile.fmcsa.dot.gov/qc/services/carriers/"
            f"{normalized_mc}?webKey={FMCSA_API_KEY}"
        )
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        return {
            "approved": False,
            "mc_number": normalized_mc,
            "reason": f"FMCSA lookup failed: {exc}",
            "data_source": "fmcsa_live",
        }

    carrier_record = _extract_carrier_record(payload)

    if not carrier_record:
        return {
            "approved": False,
            "mc_number": normalized_mc,
            "reason": "No carrier record was returned by FMCSA.",
            "data_source": "fmcsa_live",
        }

    operating_status = _extract_first_value(
        carrier_record,
        [
            "allowedToOperate",
            "status",
            "statusCode",
            "carrierOperation",
            "operatingStatus",
        ],
    )
    out_of_service = _extract_first_value(
        carrier_record,
        ["outOfServiceDate", "outOfService", "oosDate"],
    )
    safety_rating = _extract_first_value(
        carrier_record,
        ["safetyRating", "safetyRatingDate", "rating"],
    )
    carrier_name = _extract_first_value(
        carrier_record,
        ["legalName", "carrierName", "dbaName", "name"],
    )
    dot_number = _extract_first_value(
        carrier_record,
        ["dotNumber", "dotNo", "usdOTNumber"],
    )

    status_text = _normalize_text(operating_status)
    approved = (
        ("active" in status_text or "allowed" in status_text or "authorized" in status_text)
        and "inactive" not in status_text
        and "revoked" not in status_text
        and not out_of_service
    )

    reason = (
        "Carrier is active and eligible to work the load."
        if approved
        else "Carrier record is inactive, out of service, or missing operating authority."
    )

    return {
        "approved": approved,
        "mc_number": normalized_mc,
        "carrier_name": carrier_name,
        "dot_number": dot_number,
        "operating_status": operating_status or "UNKNOWN",
        "safety_rating": safety_rating or "UNKNOWN",
        "reason": reason,
        "data_source": "fmcsa_live",
    }


def _mock_verification(mc_number: str) -> dict[str, Any]:

    last_digit = int(next((char for char in reversed(mc_number) if char.isdigit()), "0"))
    approved = last_digit % 5 not in {0, 5}

    return {
        "approved": approved,
        "mc_number": mc_number,
        "carrier_name": f"Demo Carrier {mc_number}",
        "dot_number": f"DOT{mc_number[-6:]}",
        "operating_status": "ACTIVE" if approved else "OUT_OF_SERVICE",
        "safety_rating": "SATISFACTORY" if approved else "CONDITIONAL",
        "reason": (
            "Carrier approved in mock mode."
            if approved
            else "Carrier blocked in mock mode for demo purposes."
        ),
        "data_source": "fmcsa_mock",
    }


def _extract_carrier_record(payload: Any) -> Any:

    if isinstance(payload, dict):
        if "content" in payload:
            return _extract_carrier_record(payload["content"])

        for key in ("carrier", "carriers", "Carrier", "Carriers"):
            if key in payload:
                value = payload[key]
                if isinstance(value, list):
                    return value[0] if value else None
                return value

        if payload:
            return payload

    if isinstance(payload, list):
        return payload[0] if payload else None

    return None


def _extract_first_value(data: Any, candidate_keys: list[str]) -> Any:

    normalized_keys = {key.lower() for key in candidate_keys}

    if isinstance(data, dict):
        for key, value in data.items():
            if key.lower() in normalized_keys and value not in (None, "", []):
                return value

        for value in data.values():
            nested_value = _extract_first_value(value, candidate_keys)
            if nested_value not in (None, "", []):
                return nested_value

    if isinstance(data, list):
        for item in data:
            nested_value = _extract_first_value(item, candidate_keys)
            if nested_value not in (None, "", []):
                return nested_value

    return None


def _normalize_text(value: Any) -> str:

    if value is None:
        return ""

    return str(value).strip().lower()
