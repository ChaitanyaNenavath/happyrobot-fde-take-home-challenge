from __future__ import annotations

from typing import Any
from uuid import uuid4

SESSIONS: dict[str, dict[str, Any]] = {}


def create_session() -> dict[str, Any]:

    session_id = str(uuid4())
    session = {
        "session_id": session_id,
        "stage": "collect_mc_number",
        "transcript_turns": [],
        "offers": [],
        "load_options": [],
        "selected_load": None,
        "carrier": None,
        "load_preferences": {},
        "carrier_name": None,
        "closed": False,
        "result": None,
    }
    SESSIONS[session_id] = session
    return session


def get_session(session_id: str) -> dict[str, Any] | None:

    return SESSIONS.get(session_id)


def save_session(session: dict[str, Any]) -> None:

    SESSIONS[session["session_id"]] = session
