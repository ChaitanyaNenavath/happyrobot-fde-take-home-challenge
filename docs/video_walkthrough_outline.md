# Demo Video Outline

## Target Length

5 minutes

## Suggested Structure

### 1. Problem Setup

- Explain the inbound carrier sales use case.
- Describe the need to verify carriers, match loads, negotiate pricing, and log results.

### 2. Backend Demo

- Show the load data source.
- Show the carrier verification endpoint.
- Show the load search endpoint.
- Show the negotiation endpoint.
- Show the `POST /calls/process` endpoint for an end-to-end interaction.

### 3. Dashboard Demo

- Show headline KPIs.
- Show outcome breakdown.
- Show approval rate and load performance.
- Show the raw call log table.

### 4. Deployment

- Show `docker-compose.yml`.
- Show how the backend and dashboard run together.
- Explain how the same setup can move to a cloud provider.

### 5. Close

- Recap business value.
- Note the production upgrade path: live FMCSA, managed DB, HappyRobot integration.
