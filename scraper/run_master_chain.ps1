# Master chain. Sequential because catalog.db allows exactly one writer.
#
# The wait step waits on the job's CHECKPOINT, not on process liveness. A
# previous version polled for the process and treated "gone" as "finished" —
# so when a job died on a lock error the chain happily ran the next step
# against a half-finished database. Now: no process + no checkpoint progress
# means "crash", and the job is restarted.
#
#   0. episode fill        (restart on crash, wait for completion)
#   1. discover new TV
#   2. episodes for new TV
#   3. dedupe titles
#   4. classify scripted
#   5. movie releases + where-to-watch
#   6. prelinger
#   7. export + publish
$ErrorActionPreference = 'Continue'
$env:PYTHONIOENCODING = 'utf-8'

$scraper = 'G:\streaming app\scraper'
$py      = 'C:\Python314\python.exe'
$log     = Join-Path $scraper 'master_chain.log'

function Say($m) {
    $line = "[{0}] {1}" -f (Get-Date -Format 'HH:mm:ss'), $m
    Write-Output $line
    Add-Content -Path $log -Value $line
}

function PyRunning($pattern) {
    $p = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
         Where-Object { $_.CommandLine -match $pattern }
    return [bool]$p
}

# Run a python job to completion, restarting it if it dies early.
# $stateFile is the job's checkpoint; we compare `done` counts across runs.
function RunJob($script, $stateFile, $label, $maxHours) {
    $attempt = 0
    while ($true) {
        $attempt++
        if ($attempt -gt 40) { Say "$label gave up after $attempt attempts"; return }

        $before = 0
        if (Test-Path $stateFile) {
            try { $before = (Get-Content $stateFile -Raw | ConvertFrom-Json).done.Count } catch { $before = 0 }
        }

        if (-not (PyRunning $script)) {
            Say "$label not running - starting (attempt $attempt, checkpoint=$before)"
            Start-Process -FilePath $py -ArgumentList (Join-Path $scraper $script) `
                -WorkingDirectory $scraper -WindowStyle Hidden
            Start-Sleep -Seconds 25
        }

        $waited = 0
        # Was: while ($PyRunning $script) — PowerShell cannot put a bare command
        # with an argument in an expression position, so the whole file failed to
        # parse and every scheduled run since 1 Oct died instantly with a
        # SyntaxError before executing a single step. Matches line 49's style.
        while ((PyRunning $script)) {
            Start-Sleep -Seconds 45
            $waited += 45
            if ($waited % 900 -eq 0) { Say "$label still running ($([int]($waited/60)) min)" }
            if ($waited -gt 3600 * $maxHours) { Say "$label exceeded time budget"; return }
        }

        $after = 0
        if (Test-Path $stateFile) {
            try { $after = (Get-Content $stateFile -Raw | ConvertFrom-Json).done.Count } catch { $after = 0 }
        }

        if ($after -gt $before) { Say "$label finished (checkpoint $before -> $after)"; return }
        Say "$label exited without progress ($before -> $after) - restarting"
    }
}

function RunOnce($script, $label, $extraArgs) {
    Say "$label starting"
    & $py (Join-Path $scraper $script) @extraArgs 2>&1 |
        Select-Object -Last 6 | ForEach-Object { Say "  ${label}: $_" }
}

Say "=== master chain start ==="

RunJob 'ingest_tmdb_episodes'  (Join-Path $scraper '.tmdb_episodes_state.json')  'episode fill' 10
RunOnce 'discover_tmdb_tv' 'tv discovery' @('--pages','14')
RunJob 'ingest_tmdb_episodes'  (Join-Path $scraper '.tmdb_episodes_state.json')  'episode fill (new titles)' 6
RunOnce 'dedupe_titles' 'dedupe' @('--apply')
RunOnce 'classify_scripted' 'classify scripted' @()
RunOnce 'ingest_movie_releases' 'movie releases' @()
RunOnce 'ingest_prelinger' 'prelinger' @()
RunOnce 'export_worker_snapshot' 'export' @()

$ck = Join-Path $scraper 'worker_export\.r2_uploaded.json'
if (Test-Path $ck) { Move-Item $ck "$ck.stale" -Force; Say "cleared stale upload checkpoint" }

RunOnce 'upload_worker_export_to_r2' 'upload' @('--workers','3')
RunOnce 'export_catalog_seasons' 'seasons export' @()
RunOnce 'upload_seasons_to_r2' 'seasons upload' @('--workers','2')

# SEO. Was never wired in, so blogs.json last changed 27 Sep and nothing
# regenerated it after that. Runs AFTER export/upload: seo_agent.py reads the
# exported snapshot, and the catalog DB is single-writer so it must not overlap.
RunOnce 'seo_agent' 'seo' @()

Say "=== master chain done ==="
