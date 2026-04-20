# StegoShield App Monitor

$exePath = "C:\Users\17544\.openclaw\workspace\main\StegoShield\desktop-wpf\StegoShield.Desktop\bin\Debug\net8.0-windows\win-x64\StegoShield.Desktop.exe"

Write-Host "============================================="
Write-Host "    StegoShield App Monitor"
Write-Host "============================================="
Write-Host ""

Write-Host "Starting application with monitoring..."
Write-Host ""

# Start process with output capture
$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = $exePath
$processInfo.RedirectStandardOutput = $true
$processInfo.RedirectStandardError = $true
$processInfo.UseShellExecute = $false
$processInfo.CreateNoWindow = $false

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $processInfo

$process.Start() | Out-Null

Write-Host "Process started - PID: $($process.Id)"
Write-Host ""
Write-Host "Monitoring for 10 seconds..."
Write-Host ""

$timeout = 10
$checkInterval = 0.5
$elapsed = 0

while ($elapsed -lt $timeout) {
    Start-Sleep -Seconds $checkInterval
    $elapsed += $checkInterval
    
    if ($process.HasExited) {
        Write-Host "=============================================" -ForegroundColor Red
        Write-Host "CRITICAL: Process exited at $elapsed seconds!" -ForegroundColor Red
        Write-Host "Exit Code: $($process.ExitCode)" -ForegroundColor Red
        Write-Host ""
        
        $stderr = $process.StandardError.ReadToEnd()
        $stdout = $process.StandardOutput.ReadToEnd()
        
        if ($stderr) {
            Write-Host "=== STDERR (Errors) ===" -ForegroundColor Red
            Write-Host $stderr
            Write-Host ""
        }
        
        if ($stdout) {
            Write-Host "=== STDOUT (Output) ===" -ForegroundColor Yellow
            Write-Host $stdout
            Write-Host ""
        }
        
        break
    } else {
        $status = if ($process.Responding) { "OK" } else { "NOT RESPONDING" }
        Write-Host "Still running... ($elapsed s) - Status: $status"
    }
}

if (-not $process.HasExited) {
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Green
    Write-Host "SUCCESS: Application is still running!" -ForegroundColor Green
    Write-Host "Process ID: $($process.Id)"
    Write-Host "You should see the StegoShield window."
    Write-Host ""
    Write-Host "The application will continue running."
    Write-Host "Close the window or press Ctrl+C to stop."
    Write-Host "============================================="
    
    # Wait for process to exit
    $process.WaitForExit()
}

Write-Host ""
Write-Host "Press Enter to close this window..."
Read-Host
