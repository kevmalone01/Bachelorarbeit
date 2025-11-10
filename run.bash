#!/bin/bash
echo "Starting Document Processing System..."

# Start Frontend in a new terminal
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)'/frontend && echo Starting Frontend... && if [ ! -d node_modules ]; then echo Installing frontend dependencies... && npm install && echo Frontend dependencies installed.; else echo Frontend dependencies already installed.; fi && npm run dev"'

# Start Backend in a new terminal with improved error handling
osascript -e 'tell app "Terminal" to do script "cd '$(pwd)'/backend && echo Starting Backend... && if [ ! -d .venv ]; then echo Creating virtual environment... && python -m venv .venv && echo Virtual environment created.; else echo Virtual environment already exists.; fi && source .venv/bin/activate && if [ ! -d .venv/lib/python*/site-packages/flask ]; then echo Installing backend dependencies... && pip install -r requirements.txt && echo Backend dependencies installed.; else echo Backend dependencies already installed.; fi && python3 main.py"'

echo "Both services are starting in separate terminals."