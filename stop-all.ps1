# ==========================================================
# TRI-LAYER CRAWLER — STOP EVERYTHING SCRIPT
# ==========================================================
# Usage: .\stop-all.ps1
# Kills ZooKeeper/Kafka (java), all Python workers/pipeline/
# orchestrator, and the frontend (node). Elasticsearch is left
# running since it's a Windows service, not a terminal window.
# ==========================================================

Write-Host "Stopping Kafka + ZooKeeper (java processes)..." -ForegroundColor Cyan
Get-Process java -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "Stopping Python processes (orchestrator, workers, pipeline)..." -ForegroundColor Cyan
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "Stopping Node processes (frontend)..." -ForegroundColor Cyan
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "`nDone. Elasticsearch service left running (stop separately with 'Stop-Service elasticsearch-service-x64' if needed)." -ForegroundColor Green
