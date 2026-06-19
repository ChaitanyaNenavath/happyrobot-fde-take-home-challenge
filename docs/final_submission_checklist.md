# Final Submission Checklist

This checklist separates what is already completed in the repository from the last external actions still required to finish the challenge submission.

## Completed In Repo

- Inbound carrier workflow backend
- Session-based bot endpoints for web-call style interactions
- Carrier verification logic
- Load search and load pitch logic
- Up to three negotiation rounds
- Mock transfer-success closeout message
- Outcome classification and sentiment classification
- Persistent call logging
- Streamlit bot playground and metrics dashboard
- Dockerfiles and Docker Compose
- Client-facing and broker-facing documentation
- HappyRobot workflow design package

## Final External Actions Still Required

### 1. Create the Live HappyRobot Workflow

- Create a new HappyRobot workflow with a web call trigger.
- Configure it to call:
  - `POST /agent/session`
  - `POST /agent/respond`
- Use the prompt and node design from:
  - `happyrobot/workflow_package/agent_prompt.md`
  - `happyrobot/workflow_package/workflow_nodes.md`
  - `docs/happyrobot_platform_setup.md`
- Save the workflow and copy the live workflow link.
- If using HappyRobot MCP access, authenticate with either:
  - OAuth 2.1 inside an MCP client
  - or an org API key via `python backend/scripts/happyrobot_mcp_token.py`

Status: not done inside this repo.

### 2. Deploy the API Publicly

- Deploy the backend using `backend/Dockerfile`.
- Expose port `8000`.
- Configure environment variables from `backend/.env`.
- Verify the public health endpoint works.

Status: not done inside this repo.

### 3. Deploy the Dashboard Publicly

- Deploy the dashboard using `dashboard/Dockerfile`.
- Expose port `8501`.
- Verify the public dashboard loads.

Status: not done inside this repo.

### 4. Configure HTTPS in the Live Environment

- Use managed TLS from your host or reverse proxy.

Status: documented, not provisioned here.

### 5. Record the 5-Minute Demo Video

- Follow `docs/video_walkthrough_outline.md`.
- Include:
  - use case setup
  - short demo
  - dashboard walkthrough

Status: outline exists, video not recorded here.

### 6. Fill and Send Submission Links

- Public dashboard URL
- Public API URL if needed
- HappyRobot workflow link
- Code repository link
- Demo video link

Status: template added, links still need real values.

## Recommended Submission Order

1. Run `start_local.ps1` for local verification.
2. Run `backend/scripts/smoke_test.py`.
3. Deploy backend.
4. Deploy dashboard.
5. Create and test HappyRobot workflow against the public API.
6. Record demo video.
7. Fill the link template.
8. Send the client update email.

## One-Line Truth

The repository is finish-ready for local demo and handoff, but the public deployment, live HappyRobot workflow object, and final submission links still require external execution outside this workspace.
