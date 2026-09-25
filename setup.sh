#!/bin/bash

echo "🚀 Playwright Execution Farm - Setup"
echo ""

# Step 1: Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Step 2: Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Step 3: Install requirements
echo "📥 Installing Python packages..."
pip install -r requirements.txt

# Step 4: Install Playwright browsers
echo "🌐 Installing Chromium for Playwright..."
playwright install chromium

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To start the server, run:"
echo "   source venv/bin/activate"
echo "   uvicorn api.main:app --reload"
echo ""
echo "🌍 Then open: http://127.0.0.1:8000/docs"
