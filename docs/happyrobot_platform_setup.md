# HappyRobot Platform Setup

This repo now includes a workflow-ready conversational layer that matches the current backend pipeline.

## Recommended Setup

1. Use the HappyRobot web call trigger.
2. On call start, invoke `POST /agent/session`.
3. Speak the returned `response`.
4. For every carrier utterance, invoke `POST /agent/respond` with:
   - `session_id`
   - `utterance`
5. Speak the returned `response`.
6. Stop when `stage=closed`.

## Why This Fits The Current Pipeline

- The agent session manages stage transitions.
- Carrier verification is called only after MC collection.
- Load discovery happens only after successful verification.
- Negotiation is capped at three rounds.
- Final call outcomes are persisted automatically when the session closes.

## Minimal Integration Contract

- Start call: `/agent/session`
- Continue call: `/agent/respond`

You can still use the lower-level endpoints directly, but the agent endpoints are the correct interface for the HappyRobot bot layer.
