# Playwright Farm — Local Execution Agent

Run this on a machine that sits **inside** your private/UAT network — your
laptop, an internal VM, whatever can reach the app you're testing. It
connects **outbound** to the hosted server, so there's nothing to open on
your firewall, router, or NAT. No VPN, no port-forwarding.

```
Your machine (private network)          Hosted server (Railway etc.)
┌───────────────────────────┐           ┌───────────────────────────┐
│  playwright_agent.py       │  outbound │                           │
│  ── connects out ─────────►│  WSS      │   /ws/agent/{token}       │
│                             │◄──────────│   pushes jobs down        │
│  runs pytest / playwright   │  logs +   │   receives logs + result  │
│  test right here, reaches  │  result   │                           │
│  your private app directly │───────────►                           │
└───────────────────────────┘           └───────────────────────────┘
```

## 1. Install

```bash
cd agent
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## 2. Get a token

From anywhere with internet access (your own machine, curl, Postman):

```bash
curl -X POST "https://YOUR-SERVER/agents/register?name=my-laptop"
```

Response:

```json
{
  "agent_id": "agent-3f9a1c2b",
  "token": "a_long_random_token_here"
}
```

Save the token — it's consumed the moment the agent connects with it.

## 3. Run the agent

```bash
python playwright_agent.py --server https://YOUR-SERVER --token a_long_random_token_here --name my-laptop
```

Leave it running. It will print:

```
[agent] connecting to wss://YOUR-SERVER/ws/agent/...
[agent] connected. Waiting for jobs...
[agent] registered as agent-3f9a1c2b
```

It automatically reconnects with backoff if your network drops.

## 4. Send it a job

From the server side, zip up a Playwright project (Python, JS, or TS — it's
auto-detected from `package.json` / `requirements.txt`) and dispatch it:

```bash
curl -X POST "https://YOUR-SERVER/agents/agent-3f9a1c2b/run" \
  -F "file=@my-tests.zip" \
  -F "language=auto"
```

You'll get back a `job_id`. Watch it run:

```bash
curl "https://YOUR-SERVER/agents/jobs/JOB_ID"
```

or connect to `wss://YOUR-SERVER/ws/agent-job/JOB_ID` for a live log stream,
the same pattern the existing dashboard already uses for local jobs.

## Notes

- The agent only ever makes outbound HTTPS/WSS requests. Nothing listens on
  a local port, so there's no attack surface opened on your network.
- One agent handles one job at a time (`status: busy` while running). Run
  multiple agents — with different `--name` values — on different machines
  or VMs if you need more throughput.
- Reports (`playwright-report/`, `allure-results/`, `test-results/`) are
  zipped and uploaded automatically after each run; fetch them from
  `GET /agents/jobs/{job_id}/report`.
- Run it as a background service (systemd on Linux, NSSM / Task Scheduler
  on Windows, `launchd` on macOS) if you want it always-on rather than
  running in a terminal.
