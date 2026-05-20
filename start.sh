#!/bin/bash
set -e

echo "Starting StreamLine AI..."

# Load env vars if .env exists
[ -f .env ] && export $(grep -v '^#' .env | xargs)

# Create virtual env if not present
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo "StreamLine AI running at http://localhost:5050"
python app.py
