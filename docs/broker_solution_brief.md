# Acme Logistics Inbound Carrier Sales Automation

## Overview

This solution automates inbound carrier calls for load booking. It vets carriers, matches them to relevant freight, negotiates within approved pricing rules, records the interaction outcome, and provides custom reporting for sales and operations leadership.

## Business Problem

Carrier sales teams lose time on repetitive inbound interactions:

- Verifying carrier eligibility.
- Searching for the right load.
- Repeating load details.
- Handling low-value negotiation rounds.
- Manually logging call outcomes for reporting.

This build automates those steps so human reps focus on exception handling and relationship-driven work.

## Solution Summary

The system processes an inbound call in the following order:

1. Capture the carrier MC number.
2. Verify the carrier through FMCSA-compatible vetting logic.
3. Search structured load data for viable options.
4. Pitch the matched load details to the carrier.
5. Negotiate up to three rounds based on a configurable pricing ceiling.
6. If booked, return a transfer-success message for a sales handoff.
7. Classify outcome and sentiment, extract key call data, and save the interaction.

## Operational Capabilities

- Carrier vetting with mock mode for demos and live mode for production integration.
- Load search by origin, destination, and equipment type.
- Rule-based price negotiation with configurable margin and round limits.
- Outcome classification:
  - `BOOKED`
  - `NEGOTIATION_FAILED`
  - `NOT_INTERESTED`
  - `CARRIER_NOT_ELIGIBLE`
  - `NO_LOAD_FOUND`
- Sentiment classification:
  - `POSITIVE`
  - `NEUTRAL`
  - `NEGATIVE`
- Persistent storage for downstream analytics.

## Reporting

The dashboard reports:

- Total inbound calls.
- Booked loads.
- Failed or blocked calls.
- Approval rate.
- Average negotiated rate.
- Average negotiation rounds.
- Load-level interaction volume.
- Sentiment distribution.

## Security

- API key protection on every application endpoint.
- Support for HTTPS when deployed behind a reverse proxy or cloud load balancer.
- Environment-based secrets for runtime configuration.

## Deployment

The system is containerized and can be run locally with Docker Compose or deployed to cloud platforms such as Railway, Fly.io, Azure Container Apps, ECS, or Cloud Run.

## Recommended Next Production Steps

- Replace heuristic sentiment and extraction with an LLM-backed post-call processor.
- Connect the workflow directly to the HappyRobot tool layer.
- Replace SQLite with Postgres.
- Add authentication rotation, request logging, and observability.
- Deploy with managed HTTPS and persistent volumes.
