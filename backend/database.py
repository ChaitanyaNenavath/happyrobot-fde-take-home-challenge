import sqlite3
from datetime import datetime, timezone

from app.config import CALLS_DB_FILE

conn = sqlite3.connect(
    CALLS_DB_FILE,
    check_same_thread=False,
)
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

CALL_COLUMNS = {
    "mc_number": "TEXT",
    "load_id": "TEXT",
    "outcome": "TEXT",
    "sentiment": "TEXT",
    "final_rate": "REAL",
    "created_at": "TEXT",
    "carrier_approved": "INTEGER",
    "carrier_offer": "REAL",
    "counter_offer": "REAL",
    "negotiation_rounds": "INTEGER",
    "transcript": "TEXT",
    "carrier_name": "TEXT",
    "data_source": "TEXT",
}


def ensure_schema():

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS calls(
        id INTEGER PRIMARY KEY AUTOINCREMENT
        )
        """
    )

    existing_columns = {
        row["name"]
        for row in cursor.execute("PRAGMA table_info(calls)").fetchall()
    }

    for column_name, column_type in CALL_COLUMNS.items():
        if column_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE calls ADD COLUMN {column_name} {column_type}"
            )

    conn.commit()


def save_call_record(record):

    payload = {
        "mc_number": record.get("mc_number"),
        "load_id": record.get("load_id"),
        "outcome": record.get("outcome"),
        "sentiment": record.get("sentiment"),
        "final_rate": record.get("final_rate", 0),
        "created_at": record.get("created_at")
        or datetime.now(timezone.utc).isoformat(),
        "carrier_approved": int(bool(record.get("carrier_approved", False))),
        "carrier_offer": record.get("carrier_offer"),
        "counter_offer": record.get("counter_offer"),
        "negotiation_rounds": record.get("negotiation_rounds", 0),
        "transcript": record.get("transcript", ""),
        "carrier_name": record.get("carrier_name"),
        "data_source": record.get("data_source", "manual"),
    }

    columns = ", ".join(payload.keys())
    placeholders = ", ".join(["?"] * len(payload))

    cursor.execute(
        f"INSERT INTO calls ({columns}) VALUES ({placeholders})",
        tuple(payload.values()),
    )
    conn.commit()

    return cursor.lastrowid


def fetch_call_records(limit=100):

    rows = cursor.execute(
        """
        SELECT * FROM calls
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    return [dict(row) for row in rows]


ensure_schema()
