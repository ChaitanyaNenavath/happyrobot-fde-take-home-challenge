from __future__ import annotations

import json
from typing import Any

from app.config import LOADS_FILE


def load_catalog() -> list[dict[str, Any]]:

    with open(LOADS_FILE, encoding="utf-8") as file_obj:
        return json.load(file_obj)


def get_load_by_id(load_id: str) -> dict[str, Any] | None:

    for load in load_catalog():
        if load["load_id"] == load_id:
            return load

    return None


def search_loads(
    *,
    origin: str | None = None,
    destination: str | None = None,
    equipment_type: str | None = None,
    max_results: int = 3,
) -> list[dict[str, Any]]:

    if not any([origin, destination, equipment_type]):
        return []

    loads = load_catalog()
    scored_loads: list[tuple[int, dict[str, Any]]] = []

    for load in loads:
        score = 0

        if origin:
            if origin.lower() not in load["origin"].lower():
                continue
            score += 3

        if destination:
            if destination.lower() not in load["destination"].lower():
                continue
            score += 3

        if equipment_type:
            if equipment_type.lower() != load["equipment_type"].lower():
                continue
            score += 4

        scored_loads.append((score, load))

    scored_loads.sort(
        key=lambda item: (
            item[0],
            item[1]["loadboard_rate"],
        ),
        reverse=True,
    )

    return [load for _, load in scored_loads[:max_results]]


def format_load_pitch(load: dict[str, Any]) -> str:

    return (
        f"Load {load['load_id']} is a {load['equipment_type']} run from "
        f"{load['origin']} to {load['destination']}. Pickup is "
        f"{load['pickup_datetime']}, delivery is {load['delivery_datetime']}, "
        f"and the posted rate is ${load['loadboard_rate']:.2f}. Notes: {load['notes']}."
    )
