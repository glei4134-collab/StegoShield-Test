@echo off
chcp 65001 > nul
echo =============================================
echo       StegoShield 诊断工具
echo =============================================
echo.

REM 检查Python是否可用
echo [1/4] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo     ❌ Python未找到或未正确配置
    echo.
) else (
    echo     ✅ Python可用
    python --version
    echo.
)

REM 检查后端文件是否存在
echo [2/4] 检查后端文件...
set backend_path=C:\Users\17544\.openclaw\workspace\main\StegoShield\desktop\backend\run.py
if exist "%backend_path%" (
    echo     ✅ 后端文件存在
    echo     %backend_path%
    echo.
) else (
    echo     ❌ 后端文件不存在
    echo     预期位置: %backend_path%
    echo.
)

REM 检查exe文件
echo [3/4] 检查可执行文件...
set exe_path=%~dp0bin\Debug\net8.0-windows\win-x64\StegoShield.Desktop.exe
if exist "%exe_path%" (
    echo     ✅ 可执行文件存在
    echo     %exe_path%
    echo.
) else (
    echo     ❌ 可执行文件不存在
    echo     预期位置: %exe_path%
    echo.
)

REM 尝试启动应用
echo [4/4] 尝试启动应用...
echo.
echo 将打开应用窗口，请注意观察屏幕。
echo 如果应用未显示，请尝试 Alt+Tab 切换窗口。
echo.
cd /d "%~dp0bin\Debug\net8.0-windows\win-x64"
start "" "StegoShield.Desktop.exe"

echo 应用已启动！
echo 请检查屏幕上的应用窗口。
echo.
pause
