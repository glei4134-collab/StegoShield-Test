$exePath = "c:\Users\17544\.openclaw\workspace\main\StegoShield\desktop-wpf\StegoShield.Desktop\bin\Debug\net8.0-windows\win-x64\StegoShield.Desktop.exe"

Write-Host "Starting StegoShield with detailed error logging..."
Write-Host "Executable: $exePath"
Write-Host ""

$errLog = "$env:TEMP\stego_err_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$outLog = "$env:TEMP\stego_out_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

Write-Host "Error log: $errLog"
Write-Host "Output log: $outLog"
Write-Host ""

try {
    $process = Start-Process -FilePath $exePath `
                             -RedirectStandardError $errLog `
                             -RedirectStandardOutput $outLog `
                             -PassThru `
                             -WindowStyle Normal
    
    Write-Host "Process started with PID: $($process.Id)"
    Write-Host "Waiting 5 seconds for application to initialize..."
    Start-Sleep -Seconds 5
    
    if ($process.HasExited) {
        Write-Host "ERROR: Process exited immediately!"
        Write-Host "Exit Code: $($process.ExitCode)"
        Write-Host ""
        Write-Host "=== ERROR OUTPUT ===" -ForegroundColor Red
        if (Test-Path $errLog) {
            Get-Content $errLog | ForEach-Object { Write-Host $_ -ForegroundColor Red }
        } else {
            Write-Host "(No error log file found)"
        }
        
        Write-Host ""
        Write-Host "=== STANDARD OUTPUT ===" -ForegroundColor Yellow
        if (Test-Path $outLog) {
            Get-Content $outLog | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
        } else {
            Write-Host "(No output log file found)"
        }
    } else {
        Write-Host "SUCCESS: Process is running!" -ForegroundColor Green
        Write-Host "Process ID: $($process.Id)"
        Write-Host "Responding: $($process.Responding)"
    }
} catch {
    Write-Host "EXCEPTION: $_" -ForegroundColor Red
}
