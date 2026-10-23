@echo off
cd /d "%~dp0backend"
uvicorn app.main:app --port 8000
