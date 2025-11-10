#!/bin/bash
echo "Starting Document Processing System..."

# Start Frontend
(
  cd frontend
  echo "Starting Frontend..."
  if [ ! -d node_modules ]; then
    echo "Installing frontend dependencies..."
    npm install
    echo "Frontend dependencies installed."
  else
    echo "Frontend dependencies already installed."
  fi
  npm run dev
) &

# Start Backend
(
  cd backend
  echo "Starting Backend..."
  if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "Virtual environment created."
  else
    echo "Virtual environment already exists."
  fi

  source .venv/bin/activate

  if [ ! -f .venv/lib/python*/site-packages/flask/__init__.py ]; then
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
    echo "Backend dependencies installed."
  else
    echo "Backend dependencies already installed."
  fi

  export FLASK_APP=main.py
  echo "Initializing database..."
  flask init-db
  echo "Seeding database..."
  flask seed-db

  python main.py
) &

wait
echo "Both services are running."