#!/usr/bin/env bash
# Linux / macOS one-shot setup:  bash scripts/setup.sh
set -e
cd "$(dirname "$0")/.."
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
if [ "$1" = "gpu" ]; then pip install torch; else pip install torch --index-url https://download.pytorch.org/whl/cpu; fi
pip install -r requirements-dev.txt
[ -f .env ] || cp .env.example .env
echo "Setup done. Start with:  source .venv/bin/activate && python run.py"
