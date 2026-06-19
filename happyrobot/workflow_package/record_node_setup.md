# Wiring the workflow to this backend

Your built workflow currently does: verify carrier -> find load -> negotiate -> Extract -> Classify.
What it is **missing** is the final step that sends the call result to this API, so nothing
reaches the database or the dashboard. This file is the exact spec for that step plus the two
tool fixes.

---

## 1. Repoint the two tool nodes to THIS backend

In your version, `verify_carrier` and `find_available_loads` still point at a Google Sheet.
Change them to hit the deployed API instead. Replace `https://YOUR-API` with your deployed URL
and `YOUR_API_KEY` with the value of `API_KEY` from `backend/.env`.

### verify_carrier  (replaces the Sheet + "GET MC Number" node)
- Method: `POST`
- URL: `https://YOUR-API/carriers/verify`
- Header: `x-api-key: YOUR_API_KEY`
- Body (JSON):
  ```json
  { "mc_number": "{{ mc_number }}" }
  ```
- Use in prompt: carrier is eligible when the response field `approved` is `true`. Confirm the
  returned `carrier_name` with the caller.

### find_available_loads  (replaces the Sheet + "GET load" node)
Search by reference number (preferred) OR by lane + equipment.

- By reference number:
  - Method: `GET`
  - URL: `https://YOUR-API/loads/{{ reference_number }}`
  - Header: `x-api-key: YOUR_API_KEY`
- By lane + equipment:
  - Method: `POST`
  - URL: `https://YOUR-API/loads/search`
  - Header: `x-api-key: YOUR_API_KEY`
  - Body (JSON):
    ```json
    {
      "origin": "{{ origin }}",
      "destination": "{{ destination }}",
      "equipment_type": "{{ equipment_type }}",
      "max_results": 3
    }
    ```

---

## 2. ADD a "Record call" node at the very end (after Extract / Classify)

This is the piece that makes the dashboard work. Add one HTTP node as the last step.

- Method: `POST`
- URL: `https://YOUR-API/calls/record`
- Header: `x-api-key: YOUR_API_KEY`
- Body (JSON) — map each value to the matching variable from your Extract / Classify nodes:
  ```json
  {
    "mc_number":         "{{ extract.mc_number }}",
    "carrier_name":      "{{ extract.carrier_name }}",
    "load_id":           "{{ extract.load_id }}",
    "outcome":           "{{ classify.outcome }}",
    "sentiment":         "{{ extract.sentiment }}",
    "carrier_offer":     {{ extract.carrier_offer }},
    "final_rate":        {{ extract.final_rate }},
    "negotiation_rounds": {{ extract.negotiation_rounds }},
    "transcript":        "{{ call.transcript }}",
    "data_source":       "happyrobot"
  }
  ```

Notes:
- `outcome` MUST be one of: `BOOKED`, `NEGOTIATION_FAILED`, `NOT_INTERESTED`,
  `CARRIER_NOT_ELIGIBLE`, `NO_LOAD_FOUND`. The backend now uses these exact strings, so the
  Classify node labels and the Extract `outcome` field must use them too (they already do in
  your workflow JSON — just confirm the Classify node's five labels match this list).
- `sentiment` MUST be one of: `POSITIVE`, `NEUTRAL`, `NEGATIVE`.
- Numeric fields (`carrier_offer`, `final_rate`, `negotiation_rounds`) are sent without quotes.
  If your platform can only emit strings, that's fine — send `0` as a string fallback for
  empty numbers; the API coerces them.
- Only `mc_number`, `outcome`, `sentiment`, and `final_rate` are strictly required. The rest
  are optional, so partial calls (e.g. ineligible carrier with no load) still record cleanly.

---

## 3. Sentiment classification

The PDF asks for sentiment as a classification. You have two equivalent options:
- Keep capturing `sentiment` in the Extract node (simplest — already wired), OR
- Add a second Classify node with the three labels `POSITIVE / NEUTRAL / NEGATIVE` and map its
  output into the `sentiment` field above instead of `extract.sentiment`.

Either satisfies the requirement. Pick one and make the Record node read from it.
