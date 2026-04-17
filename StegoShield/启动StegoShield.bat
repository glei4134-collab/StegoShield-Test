@echo off
title StegoShield

echo.
echo ================================
echo   StegoShield
echo ================================
echo.
echo [1] Local Run
echo [2] Install Dependencies
echo [3] Exit
echo.

set /p choice=Choice (1-3):

if "%choice%"=="1" goto run
if "%choice%"=="2" goto install
if "%choice%"=="3" goto end

echo Invalid option
pause
goto end

:install
cd backend
pip install -r requirements.txt
cd ..
echo Done
pause
goto end

:run
cd backend
python run.py
goto end

:end