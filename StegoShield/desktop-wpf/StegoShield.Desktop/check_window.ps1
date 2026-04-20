# StegoShield Window Checker

Write-Host "============================================="
Write-Host "    StegoShield Window Checker"
Write-Host "============================================="
Write-Host ""

# Launch app
$exePath = "C:\Users\17544\.openclaw\workspace\main\StegoShield\desktop-wpf\StegoShield.Desktop\bin\Debug\net8.0-windows\win-x64\StegoShield.Desktop.exe"

Write-Host "[Step 1] Starting application..."
$process = Start-Process -FilePath $exePath -PassThru
Write-Host "  Process ID: $($process.Id)"
Write-Host ""

Start-Sleep -Seconds 3

Write-Host "[Step 2] Checking process status..."
if ($process.HasExited) {
    Write-Host "  X Process exited immediately!" -ForegroundColor Red
    Write-Host "  Exit Code: $($process.ExitCode)" -ForegroundColor Red
} else {
    Write-Host "  OK Process is running" -ForegroundColor Green
    Write-Host "  Responding: $($process.Responding)"
    Write-Host ""
    
    Write-Host "[Step 3] Checking window..."
    if ($process.MainWindowHandle -eq [IntPtr]::Zero) {
        Write-Host "  X No window handle found!" -ForegroundColor Red
        Write-Host "  This means the window was not created or is hidden."
    } else {
        Write-Host "  OK Window handle: $($process.MainWindowHandle)"
        Write-Host "  Window Title: $($process.MainWindowTitle)"
    }
}

Write-Host ""
Write-Host "[Step 4] Searching for all windows..."
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")]
    public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool IsIconic(IntPtr hWnd);
}
"@

$foundWindows = @()
$callback = {
    param([IntPtr]$hWnd, [IntPtr]$lParam)
    $title = New-Object System.Text.StringBuilder 256
    [Win32]::GetWindowText($hWnd, $title, 256) | Out-Null
    $titleText = $title.ToString()
    
    if ($titleText.Length -gt 0 -and ($titleText -like "*Stego*" -or $titleText -like "*Shield*")) {
        $isVisible = [Win32]::IsWindowVisible($hWnd)
        $isMinimized = [Win32]::IsIconic($hWnd)
        
        $script:foundWindows += [PSCustomObject]@{
            Handle = $hWnd
            Title = $titleText
            Visible = $isVisible
            Minimized = $isMinimized
        }
    }
    return $true
}

[Win32]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null

if ($foundWindows.Count -gt 0) {
    Write-Host "  Found $($foundWindows.Count) window(s):" -ForegroundColor Green
    foreach ($win in $foundWindows) {
        Write-Host "    Title: $($win.Title)"
        Write-Host "    Handle: $($win.Handle)"
        Write-Host "    Visible: $($win.Visible)"
        Write-Host "    Minimized: $($win.Minimized)"
        Write-Host ""
        
        if (-not $win.Visible -or $win.Minimized) {
            Write-Host "    Attempting to show window..." -ForegroundColor Yellow
            [Win32]::ShowWindow($win.Handle, 5) | Out-Null  # SW_RESTORE
            [Win32]::ShowWindow($win.Handle, 1) | Out-Null  # SW_SHOW
            [Win32]::SetForegroundWindow($win.Handle) | Out-Null
            Write-Host "    Done! Window should now be visible." -ForegroundColor Green
        }
    }
} else {
    Write-Host "  X No StegoShield windows found!" -ForegroundColor Red
    Write-Host "  The application may be running but not creating a visible window."
}

Write-Host ""
Write-Host "============================================="
Write-Host "If you still don't see the window, try:"
Write-Host "  1. Press Alt+Tab to cycle through windows"
Write-Host "  2. Check all monitors if you have multiple"
Write-Host "  3. Look for StegoShield in taskbar"
Write-Host "============================================="
