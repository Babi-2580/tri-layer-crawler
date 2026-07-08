# ==========================================================
# TRI-LAYER CRAWLER — LITE STARTUP (for low-RAM machines)
# ==========================================================
# Usage:
#   .\start-lite.ps1 surface   -> starts infra + surface worker only
#   .\start-lite.ps1 deep      -> starts infra + deep worker only
#   .\start-lite.ps1 dark      -> starts infra + dark worker only
#   .\start-lite.ps1           -> starts infra only (no worker)
#
# Unlike start-all.ps1, this launches things ONE AT A TIME with
# longer pauses between each, so you never get a CPU/RAM spike
# from many processes starting at the exact same moment.
# ==========================================================

param(
    [ValidateSet("surface", "deep", "dark", "")]
    [string]$Layer = ""
)

$ProjectRoot = "C:\Users\Babi\Downloads\tri-layer-crawler-FULL-PROJECT (1)"
$KafkaRoot   = "C:\Kafka"

function Open-Step {
    param($Title, $WorkDir, $Command, $WaitAfter = 8)
    Write-Host "`nStarting: $Title ..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$WorkDir'; Write-Host '=== $Title ===' -ForegroundColor Green; $Command"
    Write-Host "Waiting $WaitAfter s before starting the next service (keeps CPU/RAM spikes low)..." -ForegroundColor DarkGray
    Start-Sleep -Seconds $WaitAfter
}

Write-Host "========== LITE STARTUP (low-RAM friendly) ==========" -ForegroundColor Yellow

# 1. Elasticsearch service check (no new window needed, it's a Windows service)
$es = Get-Service elasticsearch-service-x64 -ErrorAction SilentlyContinue
if ($es -and $es.Status -ne 'Running') {
    Write-Host "Starting Elasticsearch service..." -ForegroundColor Yellow
    Start-Service elasticsearch-service-x64
    Write-Host "Waiting 15s for Elasticsearch to initialize..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 15
} else {
    Write-Host "Elasticsearch already running." -ForegroundColor Green
}

# 2. ZooKeeper (longer wait -- it must be fully up before Kafka)
Open-Step -Title "ZooKeeper" -WorkDir $KafkaRoot -Command ".\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties" -WaitAfter 12

# 3. Kafka (longer wait -- JVM startup + ZooKeeper handshake)
#    KAFKA_HEAP_OPTS reduces Kafka's memory footprint, lowering the
#    chance of a GC pause long enough to lose its ZooKeeper session
#    (which is what crashed it before).
Open-Step -Title "Kafka" -WorkDir $KafkaRoot -Command "`$env:KAFKA_HEAP_OPTS='-Xms256M -Xmx256M'; .\bin\windows\kafka-server-start.bat .\config\server.properties" -WaitAfter 15

# 4. Orchestrator
Open-Step -Title "Orchestrator" -WorkDir "$ProjectRoot\orchestrator" -Command ".\..\venv\Scripts\Activate.ps1; uvicorn main:app --reload --port 8000" -WaitAfter 8

# 5. Raw data pipeline consumer (needed regardless of which worker you test)
Open-Step -Title "Raw Data Pipeline" -WorkDir $ProjectRoot -Command ".\venv\Scripts\Activate.ps1; python -m pipeline.kafka_consumers.raw_data_consumer" -WaitAfter 8

# 6. ONE worker only, based on the parameter you passed in
switch ($Layer) {
    "surface" {
        Open-Step -Title "Surface Worker" -WorkDir "$ProjectRoot\workers\surface_crawlers" -Command ".\..\..\venv\Scripts\Activate.ps1; python surface_worker.py" -WaitAfter 5
    }
    "deep" {
        Open-Step -Title "Deep Worker" -WorkDir "$ProjectRoot\workers\deep_crawlers" -Command ".\..\..\venv\Scripts\Activate.ps1; python automated_scraper.py" -WaitAfter 5
    }
    "dark" {
        Open-Step -Title "Dark Worker (isolated venv_dark)" -WorkDir "$ProjectRoot\workers\dark_crawlers" -Command ".\venv_dark\Scripts\Activate.ps1; python tor_spider.py" -WaitAfter 5
        Write-Host "Reminder: make sure Tor Browser is open!" -ForegroundColor Yellow
    }
    default {
        Write-Host "No worker layer specified -- only infrastructure started." -ForegroundColor Yellow
        Write-Host "Run again with: .\start-lite.ps1 surface   (or deep / dark)" -ForegroundColor Yellow
    }
}

# 7. Frontend last
Open-Step -Title "Frontend" -WorkDir "$ProjectRoot\frontend" -Command "npm run dev" -WaitAfter 5

Write-Host "`n======================================================" -ForegroundColor Yellow
Write-Host "Done. Open http://localhost:5173 in your browser." -ForegroundColor Green
Write-Host "Only the '$Layer' worker is running (lighter on RAM)." -ForegroundColor Green
Write-Host "To test a different layer, close that worker's window" -ForegroundColor Yellow
Write-Host "and run:  .\start-lite.ps1 <surface|deep|dark>" -ForegroundColor Yellow
Write-Host "======================================================" -ForegroundColor Yellow
