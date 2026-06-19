# Updates applied (review before deploy)

## Critical fix — outcome label mismatch
Your backend used outcome labels that did **not** match the labels your HappyRobot workflow
sends. Any real call with one of the mismatched outcomes would have been rejected by the API
with a 422 error and never recorded. All five labels are now aligned to the workflow:

| Old (backend)        | New (matches workflow) |
|----------------------|------------------------|
| `INELIGIBLE_CARRIER` | `CARRIER_NOT_ELIGIBLE` |
| `NO_MATCHING_LOAD`   | `NO_LOAD_FOUND`        |
| `CARRIER_DECLINED`   | `NOT_INTERESTED`       |
| `BOOKED`             | `BOOKED` (unchanged)   |
| `NEGOTIATION_FAILED` | `NEGOTIATION_FAILED` (unchanged) |

Changed in: `backend/app/models.py`, `backend/app/services/analysis.py`,
`backend/app/services/agent.py`, `backend/scripts/seed_data.py`, `dashboard/app.py`,
`docs/broker_solution_brief.md`. Verified live: `POST /calls/record` now accepts
`CARRIER_NOT_ELIGIBLE` and `NO_LOAD_FOUND`.

## Dashboard decoupled from the database file
`dashboard/app.py` `load_calls_dataframe()` now reads call records over HTTP via `GET /calls`
(using the API URL + key from the sidebar), and falls back to the local SQLite file only if the
API is unreachable. This means the dashboard and API can run as two independent containers /
services with no shared database volume.

## Load catalog expanded (2 -> 8)
`backend/data/loads.json` now has 8 realistic loads with all 13 required fields, including
`LD005` (Columbus, OH -> Cartersville, GA reefer) which matches your agent prompt's demo script.

## Seed data enriched (3 -> 14)
`backend/scripts/seed_data.py` now inserts 14 records spanning all 5 outcomes and all 3
sentiments so the dashboard demo looks substantial. Run with `--reset` to wipe first.
The shipped `calls.db` is pre-seeded with this set.

## New: workflow record-node spec
`happyrobot/workflow_package/record_node_setup.md` — exact request bodies for repointing the two
tool nodes to this backend and for the **missing** "Record call" node that sends the Extract /
Classify output to `POST /calls/record`. This is the step that makes the dashboard populate from
real calls.

## Not changed (working as-is)
API-key auth on every endpoint, FMCSA mock/live service, negotiation rate-floor logic
(`loadboard_rate * (1 + NEGOTIATION_MARGIN)`, 3-round cap), Dockerfiles, docker-compose.
