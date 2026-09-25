# Deploying the server (no local testing required)

## First: why not Vercel?

Vercel only runs your code inside short-lived serverless functions — it
cannot keep a process alive to hold open WebSocket connections from your
agents. That's the whole mechanism this feature depends on, so Vercel
can't host this server. (It would be fine later for a separate static
dashboard, but you don't need that — `dashboard.html` is already served
directly by this FastAPI app.)

**Render** or **Railway** both run a real, persistent process, so either
works. Recommendation: **Render**, because it has an actual free tier
(Railway's "free" plan today is a 30-day trial, then ~$1/month of credit —
easy to run out of). Render's free web services do spin down after 15
minutes with no traffic, but as of Feb 2026 an open WebSocket connection
with traffic counts as activity, so a connected agent keeps it awake. A
cold start after idle time just adds ~30-60 seconds before the next
connection succeeds — the agent's reconnect loop already handles that.

I added `Dockerfile.deploy`, `requirements-deploy.txt`, and `render.yaml` to
the project for this — a slim build with no browsers on the server (the
agent installs its own browser on your machine, not here), so it builds
fast and fits comfortably in a free tier.

---

## Option A — Render (recommended, actually free)

1. Push this project to a GitHub repo (Render deploys from Git, not by file upload).
2. Go to https://dashboard.render.com → **New** → **Blueprint**.
3. Connect the repo. Render will read `render.yaml` automatically and
   propose a service called `playwright-farm-server` using
   `Dockerfile.deploy` on the **Free** plan.
4. Click **Apply** / **Deploy**. First build takes a few minutes.
5. Once live, Render gives you a URL like
   `https://playwright-farm-server.onrender.com`. Test it:
   ```bash
   curl https://playwright-farm-server.onrender.com/health
   ```
   You should get `{"status":"healthy"}`.

No `render.yaml`/Blueprint option in your account? Do it manually instead:
**New** → **Web Service** → connect the repo → set **Runtime** to
**Docker** → **Dockerfile Path** to `Dockerfile.deploy` → **Plan**: Free →
**Health Check Path**: `/health` → Deploy.

---

## Option B — Railway

The repo already has `railway.json` pointing at the full `Dockerfile`
(which installs Chromium — heavier, and not needed by the agent flow).
For the lean agent-only deploy, point it at `Dockerfile.deploy` instead:

1. Push to GitHub.
2. https://railway.app → **New Project** → **Deploy from GitHub repo** → select it.
3. In the service's **Settings** → **Build**, set **Dockerfile Path** to
   `Dockerfile.deploy` (overrides what's in `railway.json`).
4. Railway auto-detects `$PORT` and deploys. You'll get a URL like
   `https://playwright-farm-server-production.up.railway.app`.
5. Same health check: `curl .../health`.

Be aware: on Railway's current free plan you get a one-time $5 trial
credit for 30 days, then a $1/month credit afterward (0.5 GB RAM cap).
If you outgrow that, Hobby is $5/month flat and removes those caps —
worth budgeting for once this is live for real customers.

---

## After it's deployed: connect an agent from anywhere with internet

Since your deployed server now has a public URL, you don't need to test
locally at all — the agent (`agent/playwright_agent.py`) just needs to run
somewhere with internet access, e.g. your own laptop:

```bash
# 1. Get a token from the live server
curl -X POST "https://YOUR-RENDER-OR-RAILWAY-URL/agents/register?name=my-laptop"

# 2. Install and run the agent
cd agent
pip install -r requirements.txt
playwright install chromium
python playwright_agent.py --server https://YOUR-RENDER-OR-RAILWAY-URL --token PASTE_TOKEN_HERE --name my-laptop
```

You should see `[agent] connected. Waiting for jobs...` in your terminal,
and:

```bash
curl "https://YOUR-RENDER-OR-RAILWAY-URL/agents"
```

should list your agent as connected. Then dispatch a job:

```bash
zip -r demo-tests.zip tests requirements.txt   # zip the customer's test project
curl -X POST "https://YOUR-RENDER-OR-RAILWAY-URL/agents/AGENT_ID/run" -F "file=@demo-tests.zip"
curl "https://YOUR-RENDER-OR-RAILWAY-URL/agents/jobs/JOB_ID"
```

Watch the log lines appear in the agent's terminal in real time while the
job status updates on the server.

## Secrets

Don't commit real tokens or secrets to the repo. Everything this feature
needs is generated at runtime by `/agents/register` — there's nothing to
put in `.env` for this part specifically.
