import sys
from pathlib import Path

import requests
from dotenv import dotenv_values

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
ENV_VALUES = dotenv_values(BACKEND_DIR / ".env")

API_URL = "http://127.0.0.1:8000"
API_KEY = ENV_VALUES.get("API_KEY", "")


def main():

    if not API_KEY:
        raise SystemExit("API_KEY missing in backend/.env")

    headers = {"x-api-key": API_KEY}

    health = requests.get(f"{API_URL}/health", headers=headers, timeout=10)
    health.raise_for_status()

    start = requests.post(f"{API_URL}/agent/session", headers=headers, timeout=10)
    start.raise_for_status()
    session_id = start.json()["session_id"]

    utterances = [
        "My MC is 123456",
        "Dallas to Atlanta dry van",
        "I can do it for 1850",
    ]

    result = None

    for utterance in utterances:
        response = requests.post(
            f"{API_URL}/agent/respond",
            headers=headers,
            json={"session_id": session_id, "utterance": utterance},
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()

    if not result or result.get("stage") != "closed":
        raise SystemExit("Agent flow did not close correctly.")

    print("Smoke test passed.")
    print(result["result"])


if __name__ == "__main__":
    sys.path.insert(0, str(BACKEND_DIR))
    main()
