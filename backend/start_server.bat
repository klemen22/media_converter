@echo off
call venv\Scripts\activate.bat
cd /d %~dp0

echo Starting nginx...
cd nginx-1.28.0
start "" nginx.exe
cd ..

timeout /t 2 >nul

tasklist | findstr /I "nginx.exe" >nul
IF %ERRORLEVEL% EQU 0 (
    echo [OK] Nginx is running
) ELSE (
    echo [ERROR] Nginx is NOT running
)

echo Starting uvicorn...
uvicorn main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 300

pause
