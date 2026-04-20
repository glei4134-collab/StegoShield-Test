$exePath = "c:\Users\17544\.openclaw\workspace\main\StegoShield\desktop-wpf\StegoShield.Desktop\bin\Debug\net8.0-windows\win-x64\StegoShield.Desktop.exe"

Write-Host "Checking for StegoShield processes..."
$processes = Get-Process | Where-Object { $_.ProcessName -like '*StegoShield*' }

if ($processes) {
    Write-Host "Found $($processes.Count) StegoShield process(es):"
    foreach ($proc in $processes) {
        $status = if ($proc.Responding) { "Responding" } else { "Not Responding" }
        Write-Host "  - $($proc.ProcessName) (PID: $($proc.Id), Status: $status)"
    }
} else {
    Write-Host "No StegoShield processes found. Starting application..."
    Start-Process $exePath
    Start-Sleep -Seconds 3
    
    $newProcesses = Get-Process | Where-Object { $_.ProcessName -like '*StegoShield*' }
    if ($newProcesses) {
        Write-Host "SUCCESS! Application started. Found $($newProcesses.Count) process(es)"
        foreach ($proc in $newProcesses) {
            Write-Host "  - $($proc.ProcessName) (PID: $($proc.Id))"
        }
    } else {
        Write-Host "WARNING: Process started but immediately exited!"
        Write-Host "Trying to run with error output..."
        $errLog = "$env:TEMP\stego_err.log"
        Start-Process $exePath -RedirectStandardError $errLog -Wait
        if (Test-Path $errLog) {
            $errors = Get-Content $errLog
            if ($errors) {
                Write-Host "Errors found:"
                $errors | ForEach-Object { Write-Host $_ }
            } else {
                Write-Host "No error output captured"
            }
        }
    }
}
