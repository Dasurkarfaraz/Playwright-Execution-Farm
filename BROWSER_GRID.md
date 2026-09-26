# Browser Grid: customers connect their own scripts via wsEndpoint

This is the feature behind the LambdaTest-style sample you shared:

```js
const browser = await chromium.connect({
  wsEndpoint: `wss://cdp.lambdatest.com/playwright?capabilities=${...}`
})
```

Their script doesn't change how it's written — it just points at your server
instead of running a browser locally. **The browser actually runs on your
server**, and we relay Playwright's own wire protocol through a WebSocket.

## This is a genuinely different resource profile than the agent feature

Everything else in this project (the `/agents/...` dispatcher) is
intentionally lightweight — it never launches a browser itself, so it runs
fine on a free tier. This feature is the opposite: **every connected
customer session launches a real headless Chromium/Firefox/WebKit process**,
which needs roughly 300-500MB of RAM each. That will not fit on Render's or
Railway's free/tiny tiers if you expect more than one session at a time.

Recommendation: run this as a **separate service** from the lean dispatcher,
on a plan with real RAM (Render Standard, Railway Hobby+, or a small cloud
VM), and only turn it on once you've decided customers actually need it.
Keep the free dispatcher for the agent feature regardless.

## Deploying it

1. Use `requirements-deploy.txt` **plus** `requirements-browsergrid.txt`
   (has `playwright` + `websockets`).
2. Build must also run `playwright install --with-deps chromium firefox webkit`
   (this is why the image is heavier — three browser binaries, not zero).
3. Give it enough RAM per your expected concurrent session count (each live
   customer session ≈ one browser process).
4. If `playwright` isn't installed, the app still boots fine (the lean
   dispatcher keeps working) — it just returns a clear "browser grid not
   enabled" error on `/playwright`, `/browser-keys`, `/browser-sessions`
   instead of crashing.

## Issuing a customer their credentials

```bash
curl -X POST "https://YOUR-SERVER/browser-keys?user=acme-corp&name=Acme's key"
```

```json
{
  "user": "acme-corp",
  "access_key": "a_long_random_value"
}
```

## What the customer's script looks like (minimal changes from your sample)

Two changes from what you pasted: point `wsEndpoint` at your server, and use
our capability namespace, `PWFarm:Options`, instead of `LT:Options` (that
name belongs to LambdaTest specifically — using our own keeps this clearly
our product rather than looking like we're impersonating theirs).

```js
const { chromium } = require('playwright')

;(async () => {
  const capabilities = {
    browserName: 'chrome',        // chrome | pw-chromium | pw-firefox | pw-webkit | msedge
    'PWFarm:Options': {
      user: 'acme-corp',
      accessKey: 'a_long_random_value',
      build: 'Nightly Regression',
      name: 'Login flow test',
    },
  }

  const browser = await chromium.connect({
    wsEndpoint: `wss://YOUR-SERVER/playwright?capabilities=${encodeURIComponent(JSON.stringify(capabilities))}`
  })

  const page = await browser.newPage()
  await page.goto('https://duckduckgo.com')
  const title = await page.title()
  console.log(title)

  await browser.close()
})()
```

Runs from anywhere with internet — their CI, their laptop, wherever. It
just needs `playwright`/`@playwright/test` installed there as a client
library (no browser binaries needed on their end — the browser is on your
server).

## What this does NOT yet do

Being upfront about the gap between this sample script's features and what's
built so far, so nothing's overpromised:

- **`video: true` / `console: true` / `network: true`** in the original
  sample — session recording, console log capture, and network/HAR capture
  are not implemented. Those need real additional engineering (screen
  recording pipeline, CDP event capture and storage, HAR generation).
  Worth scoping separately once the core connect flow is proven.
- **Session pooling / reuse** — right now every connection launches a brand
  new browser and tears it down on disconnect. Fine for correctness, not
  optimized for cost/speed at volume.
- **Concurrency limits** — nothing currently caps how many browsers can be
  launched at once; a burst of connections could exhaust server RAM. Add a
  semaphore before this goes in front of real customers.

## Running locally instead of on our server

You separately asked about customers being able to "run on local env" too —
that's already covered by the **agent** feature (`agent/playwright_agent.py`,
the `run-local` / `run-git` / `run` dispatch modes), which is a different,
already-working mechanism: the dashboard triggers a run, and it executes on
the customer's own machine. That's the right tool for "run entirely on my
own machine." This browser-grid feature is for the opposite case: customer
keeps their own script/CI, but wants someone else's server to supply the
browser.

Making *this exact* wsEndpoint-connect flow also work against a customer's
local machine (so their own script, unmodified, could reach a browser
running on their laptop through our tunnel) is possible but meaningfully
more engineering — it'd mean relaying this same wire protocol through the
existing agent WebSocket tunnel instead of a locally-launched browser. Worth
a follow-up task if you need it; flagging it now rather than quietly
building a partial version.
