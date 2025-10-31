# Monitor ChromaDB Embedding Progress in Real-time
# Usage: powershell -ExecutionPolicy Bypass -File scripts/monitor_embedding.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "CHROMADB EMBEDDING MONITOR" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

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
$stableCount = 0
$startTime = Get-Date

Write-Host "Monitoring ChromaDB collection: chatbot_knowledge" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
Write-Host ""

while ($true) {
    $count = Get-DocumentCount
    $elapsed = (Get-Date) - $startTime
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    # Check if count is stable
    if ($count -eq $lastCount) {
        $stableCount++
    } else {
        $stableCount = 0

        # Calculate rate when count changes
        $rate = if ($elapsed.TotalSeconds -gt 0) {
            [math]::Round($count / $elapsed.TotalSeconds, 2)
        } else { 0 }

        Write-Host "[$timestamp] " -NoNewline -ForegroundColor Gray
        Write-Host "Documents in ChromaDB: " -NoNewline -ForegroundColor Green
        Write-Host "$count " -NoNewline -ForegroundColor Cyan
        Write-Host "| Rate: $rate docs/sec" -ForegroundColor Yellow

        $lastCount = $count
    }

    # If count hasn't changed for 30 seconds (6 iterations at 5s interval), consider complete
    if ($stableCount -ge 6 -and $count -gt 0) {
        Write-Host ""
        Write-Host "✅ Embedding appears complete - count stable at $count documents" -ForegroundColor Green
        Write-Host "Total time: $($elapsed.Hours)h $($elapsed.Minutes)m $($elapsed.Seconds)s" -ForegroundColor Cyan
        Write-Host ""

        # Show collection details
        Write-Host "Collection details:" -ForegroundColor Cyan
        docker exec chatbot-app python -c @"
import chromadb
client = chromadb.HttpClient(host='chromadb', port=8000)
collection = client.get_collection('chatbot_knowledge')
print(f'  Total documents: {collection.count()}')
print(f'  Collection name: {collection.name}')
"@ 2>$null

        break
    }

    Start-Sleep -Seconds 5
}

Write-Host ""
Write-Host "You can now test your embedded data:" -ForegroundColor Cyan
Write-Host '  curl -X POST http://localhost:8000/search -H "Content-Type: application/json" -d "{`"query`": `"screen list`", `"limit`": 5}"' -ForegroundColor White
