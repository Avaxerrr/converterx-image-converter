@echo off
setlocal

REM Change to script directory
cd /d "%~dp0"

REM Detect and activate venv
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo ERROR: .venv not found at .venv\Scripts\activate.bat
    pause
    exit /b 1
)

REM Optional: pin python.exe path (safer than relying on PATH)
set PYTHON_EXE=%CD%\.venv\Scripts\python.exe

REM Show which interpreter is running
"%PYTHON_EXE%" -c "import sys; print('Python:', sys.version); print('Exec:', sys.executable)"

REM Run your app
"%PYTHON_EXE%" "%CD%\main.py"
set EXITCODE=%ERRORLEVEL%

echo.
echo App exited with code %EXITCODE%
pause
exit /b %EXITCODE%
