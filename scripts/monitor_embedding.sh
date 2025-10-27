#!/bin/bash
# Monitor embedding progress in real-time

echo "=========================================="
echo "EMBEDDING PROGRESS MONITOR"
echo "=========================================="
echo ""

# Function to get ChromaDB count
get_count() {
    docker exec chatbot-app python -c "
import chromadb
try:
    client = chromadb.HttpClient(host='chromadb', port=8000)
    collection = client.get_collection('chatbot_knowledge')
    print(collection.count())
except:
    print('0')
" 2>/dev/null
}

# Monitor in a loop
while true; do
    COUNT=$(get_count)
    PROGRESS=$(echo "scale=2; $COUNT * 100 / 3606" | bc 2>/dev/null || echo "0")

    echo "$(date '+%H:%M:%S') - Documents: $COUNT / 3606 ($PROGRESS%)"

    if [ "$COUNT" -ge "3606" ]; then
        echo ""
        echo "✅ EMBEDDING COMPLETE!"
        break
    fi

    sleep 10
done
