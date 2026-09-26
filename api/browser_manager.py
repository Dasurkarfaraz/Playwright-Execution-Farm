"""
Browser Grid Manager
====================
This is a DIFFERENT execution model from the agent system in agent_manager.py.

The agent system: customer clicks "run" in our dashboard, we push a job to
their machine, their machine runs the test.

This system: the customer keeps writing and running their OWN Playwright
scripts (in their own CI, their own laptop, wherever) exactly like the
sample they showed us -

    const browser = await chromium.connect({
      wsEndpoint: `wss://OUR-SERVER/playwright?capabilities=${...}`
    })

...and the actual browser runs on OUR server instead of theirs. We launch a
real headless Chromium/Firefox/WebKit per connection using Playwright's own
launch_server() (which exposes a standard, language-agnostic WebSocket wire
protocol - any Playwright client, Node/Python/Java/.NET, can connect to it),
and we transparently relay bytes between the customer's connection and that
local browser server.

IMPORTANT TRADE-OFF: unlike the lean dispatcher server (api/main.py's
/agents endpoints), THIS feature needs real compute - launching a browser is
~300-500MB of RAM per concurrent session. It will not run on a free/tiny
tier. See BROWSER_GRID.md for deployment notes before turning this on.
"""
import asyncio
import json
import secrets
from datetime import datetime
from typing import Dict, Optional

from fastapi import WebSocket
import websockets as ws_client
from playwright.async_api import async_playwright

# Map the capability names in the customer's script to what Playwright expects.
# We use our OWN capability namespace, "PWFarm:Options", rather than copying
# a competitor's private schema name.
BROWSER_MAP = {
    "chrome": ("chromium", "chrome"),
    "chromium": ("chromium", None),
    "pw-chromium": ("chromium", None),
    "msedge": ("chromium", "msedge"),
    "microsoftedge": ("chromium", "msedge"),
    "pw-firefox": ("firefox", None),
    "firefox": ("firefox", None),
    "pw-webkit": ("webkit", None),
    "webkit": ("webkit", None),
    "safari": ("webkit", None),
}


class BrowserGridManager:
    def __init__(self):
        self._playwright = None
        self.access_keys: Dict[str, dict] = {}   # access_key -> {"user":..., "name":...}
        self.active_sessions: Dict[str, dict] = {}  # session_id -> metadata, for the dashboard to show "live now"

    # ---------- credentials ----------

    def issue_access_key(self, user: str, name: str = "") -> str:
        """Reusable key - unlike agent tokens, customers will reuse this
        across many test runs from their own scripts/CI, so it is NOT
        single-use."""
        access_key = secrets.token_urlsafe(24)
        self.access_keys[access_key] = {"user": user, "name": name, "created": datetime.utcnow().isoformat()}
        return access_key

    def validate(self, user: str, access_key: str) -> bool:
        entry = self.access_keys.get(access_key)
        return bool(entry and entry["user"] == user)

    def list_access_keys(self) -> list:
        return [{"user": v["user"], "name": v["name"], "created": v["created"], "access_key_preview": k[:8] + "..."}
                for k, v in self.access_keys.items()]

    # ---------- browser lifecycle ----------

    async def _get_playwright(self):
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        return self._playwright

    async def launch_browser_server(self, browser_name: str, channel: Optional[str] = None):
        pw = await self._get_playwright()
        launcher = getattr(pw, browser_name)  # pw.chromium / pw.firefox / pw.webkit
        kwargs = {"headless": True}
        if channel:
            kwargs["channel"] = channel
        return await launcher.launch_server(**kwargs)

    def register_session(self, session_id: str, user: str, browser_name: str, meta: dict):
        self.active_sessions[session_id] = {
            "user": user, "browser": browser_name, "started": datetime.utcnow().isoformat(), **meta
        }

    def end_session(self, session_id: str):
        self.active_sessions.pop(session_id, None)

    def list_sessions(self) -> list:
        return [{"id": k, **v} for k, v in self.active_sessions.items()]


browser_grid = BrowserGridManager()


def parse_capabilities(raw: Optional[str]) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def resolve_browser(browser_name: str):
    key = (browser_name or "chromium").lower()
    return BROWSER_MAP.get(key, ("chromium", None))


async def relay(customer_ws: WebSocket, local_ws_endpoint: str):
    """Pump messages both directions between the customer's connection and
    the local browser server. This is the actual 'tunnel' for this feature -
    two concurrent forwarding loops."""
    async with ws_client.connect(local_ws_endpoint, max_size=None) as local_ws:

        async def customer_to_local():
            try:
                while True:
                    msg = await customer_ws.receive()
                    if msg["type"] == "websocket.disconnect":
                        break
                    if "text" in msg and msg["text"] is not None:
                        await local_ws.send(msg["text"])
                    elif "bytes" in msg and msg["bytes"] is not None:
                        await local_ws.send(msg["bytes"])
            except Exception:
                pass

        async def local_to_customer():
            try:
                async for message in local_ws:
                    if isinstance(message, str):
                        await customer_ws.send_text(message)
                    else:
                        await customer_ws.send_bytes(message)
            except Exception:
                pass

        await asyncio.gather(customer_to_local(), local_to_customer())
