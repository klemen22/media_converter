call venv\Scripts\activate.bat

uvicorn main:app --host 0.0.0.0 --port 8000 --reload --timeout-keep-alive 300 || (
    echo Uvicorn crashed. Exiting...
    exit /b 1
)

pause
