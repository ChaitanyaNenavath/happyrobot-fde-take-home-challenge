import os
from pathlib import Path

import requests
from dotenv import dotenv_values

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / "backend" / ".env"
ENV_VALUES = dotenv_values(ENV_PATH)


def get_base_url(cluster: str) -> str:

    if cluster.lower() == "eu":
        return "https://platform.eu.happyrobot.ai"

    return "https://platform.happyrobot.ai"


def main():

    api_key = os.getenv("HAPPYROBOT_ORG_API_KEY") or ENV_VALUES.get(
        "HAPPYROBOT_ORG_API_KEY",
        "",
    )
    cluster = os.getenv("HAPPYROBOT_CLUSTER") or ENV_VALUES.get(
        "HAPPYROBOT_CLUSTER",
        "us",
    )

    if not api_key:
        raise SystemExit("HAPPYROBOT_ORG_API_KEY is missing in backend/.env")

    token_url = f"{get_base_url(cluster)}/api/mcp/token"

    response = requests.post(
        token_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_secret": api_key,
        },
        timeout=20,
    )
    response.raise_for_status()

    payload = response.json()
    print("HappyRobot MCP token request succeeded.")
    print(f"token_type={payload.get('token_type')}")
    print(f"expires_in={payload.get('expires_in')}")
    print(f"scope={payload.get('scope')}")
    print(f"access_token={payload.get('access_token')}")


if __name__ == "__main__":
    main()
