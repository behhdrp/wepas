@echo off
setlocal enabledelayedexpansion

REM Change to this script's directory
pushd %~dp0

REM Create venv if it doesn't exist
if not exist ".venv" (
  echo Creating virtual environment...
  py -3 -m venv .venv
)

REM Activate venv
call .venv\Scripts\activate.bat

echo Installing requirements...
pip install --upgrade pip >nul
pip install -r requirements.txt

REM Default envs (override by setting them befor
if not defined DJANGO_SECRET_KEY set DJANGO_SECRET_KEY=change-me
if not defined PUBLIC_BASE_URL set PUBLIC_BASE_URL=https://wepromo.store

REM Optional (uncomment or set before running)
REM set PAYEVO_SECRET_KEY=YOUR_PAYEVO_SECRET
REM set UTMIFY_TOKEN=YOUR_UTMIFY_TOKEN

echo Running migrations...
python manage.py migrate

echo Starting Django at http://0.0.0.0:8000 ...
python manage.py runserver 0.0.0.0:8000

popd
endlocal










