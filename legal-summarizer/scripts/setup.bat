@echo off
REM Windows one-shot setup (run from the project folder):  scripts\setup.bat
cd /d "%~dp0\.."
python -m venv .venv || goto :fail
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if /I "%1"=="gpu" (pip install torch) else (pip install torch --index-url https://download.pytorch.org/whl/cpu)
pip install -r requirements-dev.txt || goto :fail
if not exist .env copy .env.example .env
echo.
echo Setup done. Start with:  .venv\Scripts\activate  then  python run.py
exit /b 0
:fail
echo Setup failed. Check the messages above.
exit /b 1
