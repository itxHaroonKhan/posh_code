#!/bin/bash
# Script to run the backend server

echo "Starting the backend server..."

# Check if virtual environment exists, if not create one
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if not already installed
pip install -r requirements.txt

# Run the server
echo "Running the server on http://localhost:8000"
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000