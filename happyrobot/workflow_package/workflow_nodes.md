# HappyRobot Workflow Nodes

## Node 1: Web Call Trigger

- Trigger type: web call
- Goal: start the inbound call
- First action: call `POST /agent/session`

## Node 2: Greeting + MC Collection

- Speak the `response` returned by `/agent/session`
- Wait for carrier input
- Send the utterance to `POST /agent/respond`

## Node 3: Verification / Routing

- Read `stage` and `response`
- If `stage` is `collect_load_preferences`, ask the returned prompt
- If `stage` is `closed`, end call

## Node 4: Load Discovery

- Continue sending each user utterance to `/agent/respond`
- When `matched_load` is returned, speak `response` to pitch the load

## Node 5: Negotiation

- Keep looping on `/agent/respond`
- If response asks for next best offer, continue
- Stop after:
  - `stage=closed`
  - transfer-success message
  - no matching load
  - ineligible carrier
  - negotiation failed

## Node 6: Wrap-up

- If `result.outcome=BOOKED`, speak the transfer-success response
- Persist the call using the backend flow already executed by the agent
- End the call
