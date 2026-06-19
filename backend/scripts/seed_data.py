"""Seed the calls database with a realistic spread of inbound-call outcomes.

Run from the backend directory:  PYTHONPATH=. python scripts/seed_data.py
Existing rows are left in place; pass --reset to wipe first.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import conn, cursor, save_call_record  # noqa: E402

# load_id, outcome, sentiment, carrier_offer, final_rate, rounds, approved, mc, name, note
ROWS = [
    ("LD001", "BOOKED",               "POSITIVE", 1850, 1850, 1, True,  "123456", "Lone Star Freight",   "Accepted posted rate on the Dallas-Atlanta van."),
    ("LD005", "BOOKED",               "POSITIVE", 1950, 1950, 2, True,  "204517", "Buckeye Reefer Co",   "Settled mid-range on the Columbus beer load."),
    ("LD003", "BOOKED",               "NEUTRAL",  1300, 1300, 1, True,  "318822", "Coastal Flatbed",     "Took the Savannah steel run at posted."),
    ("LD002", "BOOKED",               "POSITIVE", 1700, 1700, 2, True,  "551203", "Sunshine Cold Chain", "Produce to Miami, agreed after one counter."),
    ("LD007", "BOOKED",               "POSITIVE", 1500, 1500, 1, True,  "667310", "Appalachian Lumber",  "Lumber to Memphis booked quickly."),
    ("LD004", "NEGOTIATION_FAILED",   "NEGATIVE", 1400, 0,    3, True,  "712994", "Music City Carriers", "Held above ceiling on the Nashville van."),
    ("LD002", "NEGOTIATION_FAILED",   "NEGATIVE", 2100, 0,    3, True,  "880145", "Gulf Stream Trucking","Wanted 2100 on a 1650 reefer load."),
    ("LD008", "NEGOTIATION_FAILED",   "NEUTRAL",  1450, 0,    3, True,  "905662", "River City Logistics","Power-only rate gap too wide."),
    ("LD001", "NOT_INTERESTED",       "NEUTRAL",  None, 0,    0, True,  "144028", "Plains Transport",    "Declined, route did not fit the truck."),
    ("LD006", "NOT_INTERESTED",       "NEGATIVE", None, 0,    0, True,  "233517", "Peach State Haulers",  "Passed on the Jacksonville run, rate too low to bother."),
    ("LD005", "CARRIER_NOT_ELIGIBLE", "NEUTRAL",  None, 0,    0, False, "789105", "Unverified Carrier",  "Failed FMCSA eligibility review."),
    ("LD003", "CARRIER_NOT_ELIGIBLE", "NEGATIVE", None, 0,    0, False, "400990", "Out Of Service LLC",  "Carrier flagged out of service."),
    (None,    "NO_LOAD_FOUND",        "NEUTRAL",  None, 0,    0, True,  "612340", "Empire Freight",      "No match for Boise to California flatbed."),
    (None,    "NO_LOAD_FOUND",        "NEGATIVE", None, 0,    0, True,  "509871", "Frontier Carriers",   "Requested lane not in the board today."),
]


def build(record):
    load_id, outcome, sentiment, offer, final_rate, rounds, approved, mc, name, note = record
    return {
        "mc_number": mc,
        "load_id": load_id,
        "outcome": outcome,
        "sentiment": sentiment,
        "final_rate": final_rate,
        "carrier_approved": approved,
        "carrier_offer": offer,
        "counter_offer": None if outcome == "BOOKED" else (offer and round(offer * 0.92)),
        "negotiation_rounds": rounds,
        "transcript": note,
        "carrier_name": name,
        "data_source": "seed",
    }


def main():
    if "--reset" in sys.argv:
        cursor.execute("DELETE FROM calls")
        conn.commit()
        print("Cleared existing rows.")
    for record in ROWS:
        save_call_record(build(record))
    print(f"Inserted {len(ROWS)} sample call records.")


if __name__ == "__main__":
    main()
