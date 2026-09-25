# Giving this to a customer without handing them source code

Right now, running the agent means: clone/download a folder, `pip install`,
run a `.py` file. That's fine for you, but too technical to hand a customer
and it exposes the script's source.

The fix: build the agent into **one standalone executable** with
[PyInstaller](https://pyinstaller.org/). The customer gets a single file —
`playwright-agent.exe` on Windows, or a single binary on macOS/Linux — with
a token baked in or passed as one argument. No Python, no pip, no visible
`.py` files, no folder structure to navigate.

**Be honest with yourself about what this does and doesn't do:** PyInstaller
bundles your code into a binary blob, which stops a normal customer from
casually opening it in a text editor — but it is not encryption, and a
technically determined person could still extract the bundled bytecode. If
you need real IP protection (not just a simpler UX), that's a different,
harder problem (licensing servers, code obfuscation tools, etc.) — worth
raising separately if it matters to you. For "make it a simple double-click
tool instead of a dev workflow," this is the right level of effort.

## Build it (do this once, on each target OS)

PyInstaller builds for whatever OS it runs on — so build on a Windows
machine for the `.exe`, macOS for the Mac binary, etc. You can't cross-build
a Windows exe from Linux/Mac without extra tooling.

```bash
cd agent
pip install pyinstaller
pyinstaller --onefile --name playwright-agent playwright_agent.py
```

Output lands in `agent/dist/`:
- Windows: `dist\playwright-agent.exe`
- macOS/Linux: `dist/playwright-agent`

## Hand it to the customer

Give them just:
1. The executable file
2. A one-line command to run it, with their token already filled in:

**Windows:**
```cmd
playwright-agent.exe --server https://YOUR-SERVER --token THEIR_TOKEN --name customer-machine
```

**macOS/Linux:**
```bash
./playwright-agent --server https://YOUR-SERVER --token THEIR_TOKEN --name customer-machine
```

That's the whole customer-facing experience: one file, one command, no
Python or source visible. Generate their token from the dashboard's
"Register a new agent" box and send them the exact command it prints —
you never have to explain the script itself.

## Even simpler: a tiny wrapper script

If you don't want the customer typing flags at all, bake the server URL and
their token into a `.bat` (Windows) or `.command` (Mac) file that just calls
the exe with everything pre-filled, so they can double-click it:

**run-agent.bat:**
```bat
@echo off
playwright-agent.exe --server https://YOUR-SERVER --token THEIR_TOKEN --name customer-machine
pause
```

Zip the exe + this .bat together and that's the entire install for the
customer: unzip, double-click `run-agent.bat`, done.

## Still need on the customer's machine

The exe bundles Python + your agent code, but the customer's machine still
needs, separately, whatever the *tests themselves* require:
- `git` installed, if you'll use git-source jobs
- Node.js, if their tests are JavaScript/TypeScript (`npx playwright` needs it)
- Playwright's browser binaries get installed automatically on first run

Worth testing this on a clean machine (or VM) before shipping it to a real
customer, since you can't rely on Python already being present the way you
could on your own dev machine.
