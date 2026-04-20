@echo off
chcp 65001 > nul
echo =============================================
echo       StegoShield 应用启动器
echo =============================================
echo.
echo 正在启动StegoShield...
echo.

cd /d "%~dp0bin\Debug\net8.0-windows\win-x64"

if exist "StegoShield.Desktop.exe" (
    echo 找到可执行文件！
    echo 正在启动应用...
    echo.
    start "" "StegoShield.Desktop.exe"
    echo 应用已启动！
    echo.
    echo 请检查您的屏幕，应用窗口应该会显示。
    echo.
    pause
) else (
    echo 错误：找不到StegoShield.Desktop.exe
    echo 请确保应用程序已正确编译。
    echo.
    pause
)
