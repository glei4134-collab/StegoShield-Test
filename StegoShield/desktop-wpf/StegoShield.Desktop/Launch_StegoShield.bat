@echo off
echo =============================================
echo       StegoShield Diagnostic Tool
echo =============================================
echo.

REM Check Python
echo [1/4] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo     X Python not found
    echo.
) else (
    echo     OK Python is available
    python --version
    echo.
)

REM Check backend file
echo [2/4] Checking backend file...
set backend_path=C:\Users\17544\.openclaw\workspace\main\StegoShield\desktop\backend\run.py
if exist "%backend_path%" (
    echo     OK Backend file exists
    echo     %backend_path%
    echo.
) else (
    echo     X Backend file not found
    echo     Expected: %backend_path%
    echo.
)

REM Check exe file
echo [3/4] Checking executable...
set exe_path=%~dp0bin\Debug\net8.0-windows\win-x64\StegoShield.Desktop.exe
if exist "%exe_path%" (
    echo     OK Executable exists
    echo     %exe_path%
    echo.
) else (
    echo     X Executable not found
    echo     Expected: %exe_path%
    echo.
)

REM Launch app
echo [4/4] Launching application...
echo.
echo Please look for the StegoShield window!
echo Try pressing Alt+Tab if you don't see it.
echo.
cd /d "%~dp0bin\Debug\net8.0-windows\win-x64"
start "" "StegoShield.Desktop.exe"

echo.
echo App launched!
echo.
pause
