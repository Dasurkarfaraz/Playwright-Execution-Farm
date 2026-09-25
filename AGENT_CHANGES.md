# What changed: real local-execution agent

The old `api/tunnel_manager.py` only simulated a tunnel (it returned a fake
URL and never actually connected anywhere). This update adds a working
version of the feature you described: a small script customers run on their
own machine that connects **outbound** to the hosted server and executes
tests locally.

## New files
- `api/agent_manager.py` — tracks connected agents, issues connection
  tokens, dispatches jobs over WebSocket, collects logs/results.
- `agent/playwright_agent.py` — the script the customer runs. Connects out,
  downloads the test bundle, auto-detects Python/JS/TS, installs deps,
  runs the tests, streams logs live, uploads the report.
- `agent/requirements.txt`, `agent/README.md` — setup for the agent side.

## Changed files
- `api/main.py` — added the agent endpoints (see below), wired in
  `agent_manager`.

## New API endpoints
| Method | Path | What it does |
|---|---|---|
| POST | `/agents/register?name=...` | Issue a connection token for a new agent |
| GET | `/agents` | List connected agents and their status |
| WS | `/ws/agent/{token}` | The agent's persistent outbound connection |
| POST | `/agents/{agent_id}/run` | Dispatch a zipped test project to that agent |
| GET | `/agents/downloads/{filename}` | Agent fetches the test bundle |
| GET | `/agents/jobs/{job_id}` | Poll job status/logs |
| WS | `/ws/agent-job/{job_id}` | Live log stream for the dashboard |
| POST | `/agents/jobs/{job_id}/report` | Agent uploads its report zip |
| GET | `/agents/jobs/{job_id}/report` | Download that report |

`api/tunnel_manager.py` is left in place (some old endpoints still reference
it) but the agent path above is the one that actually works end to end.

## What I could not test here
This sandbox has no outbound internet access, so I could not spin up the
server and a real agent and watch a job run live. I did syntax-check every
file (`python -m py_compile`) and traced the message flow by hand. Test it
for real with the steps below before relying on it.

## How to test it for real (5 minutes, all local)

Terminal 1 — run the server:
```bash
cd playwright-farm
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Terminal 2 — get a token and start an agent:
```bash
curl -X POST "http://127.0.0.1:8000/agents/register?name=test-agent"
# copy the "token" from the response
cd agent
pip install -r requirements.txt
python playwright_agent.py --server http://127.0.0.1:8000 --token PASTE_TOKEN_HERE --name test-agent
```

Terminal 3 — send it a job (zip your `tests/` folder first):
```bash
cd playwright-farm
zip -r demo-tests.zip tests requirements.txt
curl -X POST "http://127.0.0.1:8000/agents/test-agent-XXXXXXXX/run" -F "file=@demo-tests.zip"
# use the real agent_id printed by /agents/register
curl "http://127.0.0.1:8000/agents/jobs/JOB_ID"
```

You should see the test run logs appear in Terminal 2 (the agent) and be
retrievable through Terminal 3 (the API). Once that works locally, deploy
`api/` to your host (Railway/Render/Fly/etc.) and point `--server` at the
public URL instead of `127.0.0.1`.
