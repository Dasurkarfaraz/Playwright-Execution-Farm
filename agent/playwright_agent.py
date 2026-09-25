#!/usr/bin/env python3
"""
Playwright Farm - Local Execution Agent
========================================
Run this on YOUR OWN machine (or a machine inside your private/UAT network).
It connects OUTBOUND to the hosted server over WebSocket, so you do not need
to open any inbound port, configure port-forwarding, or touch a firewall.

Once connected, the server can send this agent a job, from one of three
sources:
  - upload: a zip uploaded through the dashboard (downloaded from the server)
  - git: a repo URL the agent clones itself - your code goes straight from
    your git host to this machine, never touching the server
  - local: nothing is sent at all - runs whatever's already at --local-path
    on this machine. Use this if you don't want code leaving the machine.

For any of the three, the agent then:
  1. gets the test project (download/clone/already-there)
  2. detects whether it's Python, JavaScript or TypeScript
  3. installs dependencies + browsers if needed
  4. runs the tests, streaming every log line back to the server live
  5. zips up the report/results folder and uploads it back
  6. reports pass/fail

Usage:
    python playwright_agent.py --server https://your-app.up.railway.app --token AGENT_TOKEN --name my-laptop

Get a token first by calling, from anywhere:
    curl -X POST "https://your-app.up.railway.app/agents/register?name=my-laptop"
"""
import argparse
import asyncio
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    import requests
    import websockets
except ImportError:
    print("Missing dependencies. Run: pip install -r requirements.txt")
    sys.exit(1)


class Agent:
    def __init__(self, server: str, token: str, name: str, local_path: str = None):
        self.http_base = server.rstrip("/")
        self.ws_base = self.http_base.replace("https://", "wss://").replace("http://", "ws://")
        self.token = token
        self.name = name
        self.local_path = Path(local_path).resolve() if local_path else None
        self.ws = None

    # ---------- connection lifecycle ----------

    async def run_forever(self):
        backoff = 2
        while True:
            try:
                await self._connect_and_serve()
                backoff = 2  # reset after a clean session
            except (ConnectionRefusedError, OSError) as e:
                print(f"[agent] could not reach server ({e}); retrying in {backoff}s")
            except Exception as e:
                print(f"[agent] connection dropped ({e}); retrying in {backoff}s")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)

    async def _connect_and_serve(self):
        url = f"{self.ws_base}/ws/agent/{self.token}"
        print(f"[agent] connecting to {url}")
        async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
            self.ws = ws
            print("[agent] connected. Waiting for jobs...")
            async for raw in ws:
                msg = json.loads(raw)
                await self._handle(msg)

    async def _handle(self, msg: dict):
        mtype = msg.get("type")
        if mtype == "registered":
            print(f"[agent] registered as {msg['agent_id']}")
        elif mtype == "job":
            await self._run_job(msg)
        elif mtype == "error":
            print(f"[agent] server error: {msg.get('message')}")
            sys.exit(1)

    # ---------- job execution ----------

    async def _run_job(self, msg: dict):
        job_id = msg["job_id"]
        source = msg.get("source", "upload")
        language = msg.get("language", "auto")
        command = msg.get("command")

        workdir = Path(tempfile.mkdtemp(prefix=f"pwjob_{job_id}_"))
        try:
            if source == "local":
                if not self.local_path or not self.local_path.exists():
                    await self._log(job_id, f"ERROR: this agent was not started with --local-path, "
                                             f"or the path doesn't exist ({self.local_path})")
                    await self._send({"type": "result", "job_id": job_id, "status": "failed", "exit_code": -1})
                    return
                await self._log(job_id, f"Using local test folder: {self.local_path}")
                src = self.local_path  # never touched/deleted - it's the customer's own folder

            elif source == "git":
                git_url = msg["git_url"]
                git_ref = msg.get("git_ref") or "main"
                await self._log(job_id, f"Cloning {git_url} ({git_ref})...")
                src = workdir / "src"
                proc = await asyncio.create_subprocess_exec(
                    "git", "clone", "--depth", "1", "--branch", git_ref, git_url, str(src),
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
                )
                out, _ = await proc.communicate()
                if proc.returncode != 0:
                    await self._log(job_id, out.decode(errors="replace"))
                    await self._send({"type": "result", "job_id": job_id, "status": "failed", "exit_code": proc.returncode})
                    return

            else:  # "upload" - default, existing behavior
                download_url = msg["download_url"]
                await self._log(job_id, "Downloading test bundle...")
                zip_path = workdir / "bundle.zip"
                resp = requests.get(f"{self.http_base}{download_url}", timeout=60)
                resp.raise_for_status()
                zip_path.write_bytes(resp.content)

                src = workdir / "src"
                src.mkdir()
                with zipfile.ZipFile(zip_path) as z:
                    z.extractall(src)

            detected = language if language and language != "auto" else self._detect_language(src)
            await self._log(job_id, f"Detected project type: {detected}")

            await self._log(job_id, "Installing dependencies (first run may take a while)...")
            self._setup_env(src, detected)

            cmd = command or self._default_command(detected)
            await self._log(job_id, f"Running: {cmd}")
            exit_code = await self._stream_subprocess(job_id, cmd, cwd=src)

            report_zip = self._package_report(src, workdir)
            if report_zip:
                await self._log(job_id, "Uploading report...")
                self._upload_report(job_id, report_zip)
            else:
                await self._log(job_id, "No report/results folder found to upload.")

            status = "passed" if exit_code == 0 else "failed"
            await self._send({"type": "result", "job_id": job_id, "status": status, "exit_code": exit_code})
            await self._log(job_id, f"Job finished: {status} (exit code {exit_code})")

        except Exception as e:
            await self._send({"type": "result", "job_id": job_id, "status": "failed", "exit_code": -1})
            await self._log(job_id, f"ERROR: {e}")
        finally:
            # workdir is always our own temp scratch dir, never the customer's
            # --local-path folder, so this is always safe to delete.
            shutil.rmtree(workdir, ignore_errors=True)

    # ---------- language detection + setup ----------

    def _detect_language(self, src: Path) -> str:
        if (src / "package.json").exists():
            try:
                pkg = json.loads((src / "package.json").read_text())
            except Exception:
                pkg = {}
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "typescript" in deps or list(src.rglob("*.ts")):
                return "typescript"
            return "javascript"
        return "python"

    def _setup_env(self, src: Path, language: str):
        if language == "python":
            if (src / "requirements.txt").exists():
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
                    cwd=src, check=False
                )
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"],
                cwd=src, check=False
            )
        else:  # javascript / typescript
            if (src / "package.json").exists():
                subprocess.run(["npm", "install", "--silent"], cwd=src, check=False)
            subprocess.run(["npx", "playwright", "install", "--with-deps", "chromium"], cwd=src, check=False)

    def _default_command(self, language: str) -> str:
        if language == "python":
            return "pytest -v -s --tb=short"
        return "npx playwright test"

    # ---------- subprocess streaming ----------

    async def _stream_subprocess(self, job_id: str, cmd: str, cwd: Path) -> int:
        process = await asyncio.create_subprocess_shell(
            cmd, cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        async for raw_line in process.stdout:
            line = raw_line.decode(errors="replace").rstrip()
            if line:
                await self._log(job_id, line)
        return await process.wait()

    # ---------- report packaging ----------

    def _package_report(self, src: Path, workdir: Path):
        candidates = [src / "playwright-report", src / "allure-results", src / "test-results"]
        existing = [c for c in candidates if c.exists()]
        if not existing:
            return None
        report_zip = workdir / "report.zip"
        with zipfile.ZipFile(report_zip, "w", zipfile.ZIP_DEFLATED) as z:
            for folder in existing:
                for f in folder.rglob("*"):
                    if f.is_file():
                        z.write(f, f.relative_to(src))
        return report_zip

    def _upload_report(self, job_id: str, report_zip: Path):
        with open(report_zip, "rb") as f:
            requests.post(
                f"{self.http_base}/agents/jobs/{job_id}/report",
                files={"file": ("report.zip", f, "application/zip")},
                timeout=120,
            )

    # ---------- comms back to server ----------

    async def _log(self, job_id: str, message: str):
        print(f"[job {job_id}] {message}")
        await self._send({"type": "log", "job_id": job_id, "message": message})

    async def _send(self, payload: dict):
        if self.ws is not None:
            try:
                await self.ws.send(json.dumps(payload))
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="Playwright Farm local execution agent")
    parser.add_argument("--server", required=True, help="e.g. https://your-app.up.railway.app")
    parser.add_argument("--token", required=True, help="token from POST /agents/register")
    parser.add_argument("--name", default="local-agent", help="display name for this agent")
    parser.add_argument("--local-path", default=None,
                         help="folder on THIS machine that already has the Playwright project. "
                              "Required only if you'll dispatch 'local' jobs (code never leaves this machine).")
    args = parser.parse_args()

    agent = Agent(args.server, args.token, args.name, local_path=args.local_path)
    try:
        asyncio.run(agent.run_forever())
    except KeyboardInterrupt:
        print("\n[agent] stopped.")


if __name__ == "__main__":
    main()
