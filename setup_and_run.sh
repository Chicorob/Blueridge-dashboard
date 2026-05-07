#!/bin/bash
echo "============================================"
echo " BlueRidge Life Sciences Dashboard Setup"
echo "============================================"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "============================================"
echo " Starting Dashboard..."
echo "============================================"
echo ""
echo "Dashboard will open in your browser at http://localhost:8501"
echo "Press Ctrl+C to stop the server."
echo ""

streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
