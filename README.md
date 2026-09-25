# Playwright Execution Farm - MVP

A remote test execution platform built with FastAPI and Playwright.

## Setup (Steps 1-7)

### Step 1: Create the project ✅
```
playwright-farm/
├── api/
├── worker/
├── tests/
├── uploads/
├── results/
├── requirements.txt
└── README.md
```

### Step 2: Install Python packages

Create a virtual environment:

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Install Chromium for Playwright:
```bash
playwright install chromium
```

### Step 3: Demo test ✅
Created: `tests/test_demo.py`

This is a fake test to prove the execution engine works before connecting to a real application.

### Step 4: Worker ✅
Created: `worker/runner.py` and `worker/__init__.py`

The worker runs pytest and captures output.

### Step 5: API ✅
Created: `api/main.py`

FastAPI server with two endpoints:
- `GET /` — Health check
- `POST /run` — Execute the test

### Step 6: Start the server

```bash
uvicorn api.main:app --reload
```

You'll see:
```
Uvicorn running on http://127.0.0.1:8000
```

### Step 7: Run a test remotely

1. Open http://127.0.0.1:8000/docs
2. Click **POST /run**
3. Click **Try it out → Execute**
4. Watch for:
```json
{
    "status": "completed",
    "exit_code": 0
}
```

✅ **Step 1 Done!** When you see `exit_code: 0`, the basic MVP is working.

---

## Next Steps

Once this works, we'll add:
- **WebSocket** for live logs
- **Job queue** tracking
- **ZIP upload** support
- **Docker** deployment
- **Railway** hosting
