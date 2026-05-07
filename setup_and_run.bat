@echo off
echo ============================================
echo  BlueRidge Life Sciences Dashboard Setup
echo ============================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo ============================================
echo  Starting Dashboard...
echo ============================================
echo.
echo Dashboard will open in your browser at http://localhost:8501
echo Press Ctrl+C to stop the server.
echo.

streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false

pause
