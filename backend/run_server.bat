@echo off
REM Script to run the backend server on Windows

echo Starting the backend server...

REM Check if virtual environment exists, if not create one
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if not already installed
pip install -r requirements.txt

REM Run the server
echo Running the server on http://localhost:8000
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause