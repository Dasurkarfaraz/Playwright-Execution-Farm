@echo off
echo 🚀 Playwright Execution Farm - Setup
echo.

REM Step 1: Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Step 2: Activate virtual environment
echo ✅ Activating virtual environment...
call venv\Scripts\activate.bat

REM Step 3: Install requirements
echo 📥 Installing Python packages...
pip install -r requirements.txt

REM Step 4: Install Playwright browsers
echo 🌐 Installing Chromium for Playwright...
playwright install chromium

echo.
echo ✅ Setup complete!
echo.
echo 🚀 To start the server, run:
echo    venv\Scripts\activate.bat
echo    uvicorn api.main:app --reload
echo.
echo 🌍 Then open: http://127.0.0.1:8000/docs
