@echo off
setlocal
cd /d "%~dp0\config"

echo Installing backend requirements...
..\venv\Scripts\python.exe -m pip install -r ..\requirements.txt
if errorlevel 1 (
  echo Failed to install requirements.
  pause
  exit /b 1
)

echo Running migrations...
..\venv\Scripts\python.exe manage.py migrate
if errorlevel 1 (
  echo Migration failed.
  pause
  exit /b 1
)

echo Seeding books database...
..\venv\Scripts\python.exe manage.py seed_books

echo Starting Django server at http://127.0.0.1:8000
..\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload

endlocal
