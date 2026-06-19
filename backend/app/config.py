import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = ROOT_DIR / "docs"
LOADS_FILE = DATA_DIR / "loads.json"
CALLS_DB_FILE = DATA_DIR / "calls.db"

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("API_KEY", "local-demo-api-key")
FMCSA_API_KEY = os.getenv("FMCSA_API_KEY", "")
FMCSA_MOCK_MODE = os.getenv("FMCSA_MOCK_MODE", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
NEGOTIATION_MARGIN = float(os.getenv("NEGOTIATION_MARGIN", "0.10"))
NEGOTIATION_MAX_ROUNDS = int(os.getenv("NEGOTIATION_MAX_ROUNDS", "3"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))
