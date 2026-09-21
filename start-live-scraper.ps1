# Start the Python live scraper on :7800 with a watchdog that auto-restarts on crash.
# Usage: powershell -ExecutionPolicy Bypass -File "G:\streaming app\start-live-scraper.ps1"

$ErrorActionPreference = 'Stop'
$PY = 'C:\Users\Lucifer\AppData\Local\Python\pythoncore-3.14-64\python.exe'
$SCRIPT = 'G:\streaming app\scraper\live_service.py'
$LOG = 'G:\streaming app\live-scraper.log'
$PORT = 7800

if (-not (Test-Path $PY)) {
    Write-Error "Python not found at $PY"
    exit 1
}

# Kill any previous python process bound to :7800
Get-NetTCPConnection -State Listen -LocalPort $PORT -ErrorAction SilentlyContinue |
    ForEach-Object {
        try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
    }
Start-Sleep -Seconds 1

"=== $(Get-Date -Format 'o') === watchdog starting $SCRIPT on :$PORT" | Out-File -FilePath $LOG -Append

$attempt = 0
while ($true) {
    $attempt += 1
    "--- attempt $attempt at $(Get-Date -Format 'o') ---" | Out-File -FilePath $LOG -Append

    $p = Start-Process -FilePath $PY `
        -ArgumentList @($SCRIPT) `
        -RedirectStandardOutput $LOG `
        -RedirectStandardError "$LOG.err" `
        -WorkingDirectory (Split-Path $SCRIPT) `
        -NoNewWindow -PassThru

    # Wait for it to come up or crash
    $up = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        if ($p.HasExited) { break }
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:$PORT/health" -UseBasicParsing -TimeoutSec 1
            if ($r.StatusCode -eq 200) { $up = $true; break }
        } catch {}
    }

    if (-not $p.HasExited -and $up) {
        "[watchdog] live-scraper up on :$PORT (PID $($p.Id))" | Out-File -FilePath $LOG -Append
        # Now wait for the process to exit; restart only on non-zero / non-SIGINT exits
        $p.WaitForExit()
        $code = $p.ExitCode
        "[watchdog] live-scraper exited code=$code at $(Get-Date -Format 'o'); restarting in 3s" | Out-File -FilePath $LOG -Append
        Start-Sleep -Seconds 3
    } else {
        "[watchdog] live-scraper failed to start (exit=$($p.ExitCode)) at $(Get-Date -Format 'o'); tail of err log:" | Out-File -FilePath $LOG -Append
        if (Test-Path "$LOG.err") {
            Get-Content "$LOG.err" -Tail 30 | Out-File -FilePath $LOG -Append
        }
        Start-Sleep -Seconds 5
    }
}
