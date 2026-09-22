@echo off
REM ---------------------------------------------------------------------------
REM Launch System Monitor from source, using the project's virtual environment.
REM
REM Double-click this file, or run it from a terminal:  run.bat --debug
REM
REM pythonw.exe is used so no console window stays open behind the dashboard.
REM Pass --debug to get a console window with live log output while it runs.
REM ---------------------------------------------------------------------------
setlocal
cd /d "%~dp0"

set "PYTHONW=.venv\Scripts\pythonw.exe"
set "PYTHON=.venv\Scripts\python.exe"

if not exist "%PYTHON%" goto :no_venv

if /i "%~1"=="--debug" (
    "%PYTHON%" "main.py" %*
    goto :end
)

if exist "%PYTHONW%" (
    start "" "%PYTHONW%" "main.py" %*
    goto :end
)

start "" "%PYTHON%" "main.py" %*
goto :end

:no_venv
echo.
echo   The virtual environment was not found in:
echo   %CD%
echo.
echo   Create it and install the dependencies first:
echo.
echo       python -m venv .venv
echo       .venv\Scripts\python.exe -m pip install -r requirements.txt
echo.
echo   Or run the already-built executable instead:
echo       dist\SystemMonitor\SystemMonitor.exe
echo.
pause
exit /b 1

:end
endlocal
