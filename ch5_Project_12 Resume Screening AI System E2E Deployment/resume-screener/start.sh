#!/usr/bin/env bash
cd "$(dirname "$0")/backend" && uvicorn app.main:app --port 8000
