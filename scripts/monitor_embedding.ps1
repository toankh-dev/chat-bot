# Monitor Embedding Progress in Real-time
# Usage: powershell -ExecutionPolicy Bypass -File scripts/monitor_embedding.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "EMBEDDING PROGRESS MONITOR" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$target = 3606

function Get-DocumentCount {
    try {
        $count = docker exec chatbot-app python -c @"
import chromadb
try:
    client = chromadb.HttpClient(host='chromadb', port=8000)
    collection = client.get_collection('chatbot_knowledge')
    print(collection.count())
except Exception as e:
    print('0')
"@ 2>$null

        return [int]$count
    }
    catch {
        return 0
    }
}

$lastCount = 0
$startTime = Get-Date

Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
Write-Host ""

while ($true) {
    $count = Get-DocumentCount
    $progress = [math]::Round(($count / $target) * 100, 2)
    $remaining = $target - $count
    $elapsed = (Get-Date) - $startTime

    # Clear line and show progress
    $timestamp = Get-Date -Format "HH:mm:ss"

    if ($count -ne $lastCount) {
        $rate = if ($elapsed.TotalSeconds -gt 0) {
            [math]::Round(($count - 0) / $elapsed.TotalSeconds, 2)
        } else { 0 }

        $eta = if ($rate -gt 0) {
            $remainingSeconds = $remaining / $rate
            $etaTime = [TimeSpan]::FromSeconds($remainingSeconds)
            "$($etaTime.Hours)h $($etaTime.Minutes)m $($etaTime.Seconds)s"
        } else { "calculating..." }

        Write-Host "[$timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "Documents: $count / $target " -NoNewline -ForegroundColor Green
        Write-Host "($progress%) " -NoNewline -ForegroundColor Cyan
        Write-Host "| Rate: $rate docs/sec " -NoNewline -ForegroundColor Yellow
        Write-Host "| ETA: $eta" -ForegroundColor Magenta

        $lastCount = $count
    }

    if ($count -ge $target) {
        Write-Host ""
        Write-Host "✅ EMBEDDING COMPLETE! ($count documents)" -ForegroundColor Green
        Write-Host "Total time: $($elapsed.Hours)h $($elapsed.Minutes)m $($elapsed.Seconds)s" -ForegroundColor Cyan
        break
    }

    Start-Sleep -Seconds 5
}

Write-Host ""
Write-Host "You can now test your embedded data:" -ForegroundColor Cyan
Write-Host '  curl -X POST http://localhost:8000/search -H "Content-Type: application/json" -d "{`"query`": `"screen list`", `"limit`": 5}"' -ForegroundColor White
