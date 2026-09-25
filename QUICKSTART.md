# 🚀 Quick Start - Steps 1-7

## Your Mission
Get `exit_code: 0` from the `/run` endpoint. When you see that, you're done with MVP.

---

## Step 0: Copy Files to Your Machine

I've created the complete structure for you:

```
playwright-farm/
├── api/
│   ├── __init__.py
│   └── main.py           ← FastAPI server
├── worker/
│   ├── __init__.py
│   └── runner.py         ← Pytest executor
├── tests/
│   └── test_demo.py      ← Demo test (fake, no browser yet)
├── uploads/
├── results/
├── requirements.txt      ← Dependencies
├── setup.sh              ← macOS/Linux setup
├── setup.bat             ← Windows setup
└── README.md
```

**Copy the entire `playwright-farm/` folder to your computer.**

---

## Step 1: Setup (3 minutes)

### macOS/Linux:
```bash
cd playwright-farm
chmod +x setup.sh
./setup.sh
```

### Windows:
```bash
cd playwright-farm
setup.bat
```

### Manual Setup (all OS):
```bash
# Create virtual environment
python -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Chromium for Playwright
playwright install chromium
```

You'll see lots of downloads. **This is normal.** Playwright needs Chromium.

---

## Step 2: Start the API Server (2 minutes)

```bash
# Make sure venv is activated (you should see (venv) in your terminal)
uvicorn api.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**Leave this terminal running.** ✅

---

## Step 3: Test Locally (1 minute)

Open a **new terminal tab/window** (keep the server running):

```bash
# Test the health endpoint
curl http://127.0.0.1:8000
```

Should return:
```json
{"message":"Playwright Execution Farm"}
```

✅ **API is alive!**

---

## Step 4: Run a Test via FastAPI Docs (2 minutes)

1. **Open your browser:**
   ```
   http://127.0.0.1:8000/docs
   ```

2. You'll see the **FastAPI interactive docs** with:
   - `GET /` (home)
   - `POST /run` (run test)

3. **Click on `POST /run`**

4. Click **"Try it out"**

5. Click **"Execute"**

6. **Watch the logs** in your server terminal:
   ```
   Opening application...
   Entering username...
   Entering password...
   Clicking login...
   Login successful
   ```

7. **See the response:**
   ```json
   {
     "status": "completed",
     "exit_code": 0
   }
   ```

---

## ✅ Step 1 Complete!

When you see `exit_code: 0`, the MVP works. 

**Tell me: "Step 1 done"** and we'll build the **live execution feed with WebSocket** next.

---

## 🐛 Troubleshooting

### "Module not found: worker"
- Make sure you're running from the `playwright-farm/` root folder
- Check that `worker/__init__.py` exists

### "pytest not found"
- Run: `pip install pytest`

### "Playwright not installed"
- Run: `playwright install chromium`

### "Port 8000 already in use"
```bash
uvicorn api.main:app --reload --port 8001
```
Then use `http://127.0.0.1:8001` instead.

### "venv not activating"
Try:
```bash
# macOS/Linux
source venv/bin/activate

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat
```

---

## Architecture So Far

```
Your Computer
   │
   ├── FastAPI Server (port 8000)
   │   └── /run endpoint
   │
   └── Pytest Worker
       └── tests/test_demo.py
```

**Next:** We'll add WebSocket so you see logs **live** as they happen.
