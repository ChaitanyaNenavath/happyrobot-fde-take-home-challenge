# HappyRobot MCP Authentication

Based on the HappyRobot MCP documentation you provided, there are two authentication paths.

## 1. User OAuth 2.1

Use this when connecting Claude Code, Claude Desktop, or another MCP client directly to HappyRobot.

Relevant endpoints:

- US workflows MCP: `https://mcp.platform.happyrobot.ai/workflows/mcp`
- US combined MCP: `https://mcp.platform.happyrobot.ai/mcp`
- EU workflows MCP: `https://mcp.platform.eu.happyrobot.ai/workflows/mcp`

What happens:

1. Add the MCP server to your client.
2. Authenticate in the browser.
3. Select the HappyRobot workspace.
4. Authorize access.

This repo cannot complete the browser OAuth flow for you, but it includes the workflow and prompt assets needed once you are inside the workspace.

## 2. Service-to-Service Auth

Use this when you want a backend script or CI/CD pipeline to access HappyRobot MCP with an org API key.

### Required env vars

Add these to `backend/.env`:

```env
HAPPYROBOT_ORG_API_KEY=sk_live_your_key_here
HAPPYROBOT_CLUSTER=us
```

Use `eu` if your org is on the EU cluster.

### Local helper script

Run:

```bash
python backend/scripts/happyrobot_mcp_token.py
```

This exchanges your org API key for an MCP bearer token using the documented client credentials grant.

### Token endpoint

- US: `https://platform.happyrobot.ai/api/mcp/token`
- EU: `https://platform.eu.happyrobot.ai/api/mcp/token`

### After token retrieval

Use the returned bearer token to call the HappyRobot MCP server from your own MCP-compatible integration.

## What This Means For This Project

To finish the live HappyRobot part, you still need one of the following:

- login access to the HappyRobot workspace so you can create the workflow via OAuth-connected tooling
- or an org-level HappyRobot API key so you can authenticate service-to-service

This repo already includes the workflow-side materials:

- `happyrobot/workflow_package/agent_prompt.md`
- `happyrobot/workflow_package/workflow_nodes.md`
- `happyrobot/workflow_package/tool_contracts.json`
- `docs/happyrobot_platform_setup.md`
