#!/bin/bash
# Monitor ChromaDB embedding progress in real-time

echo "=========================================="
echo "CHROMADB EMBEDDING MONITOR"
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
except Exception as e:
    print('0')
" 2>/dev/null
}

# Get initial count
PREV_COUNT=0
STABLE_COUNT=0

echo "Monitoring ChromaDB collection: chatbot_knowledge"
echo "Press Ctrl+C to stop"
echo ""

# Monitor in a loop
while true; do
    COUNT=$(get_count)

    # Check if count changed
    if [ "$COUNT" -eq "$PREV_COUNT" ]; then
        STABLE_COUNT=$((STABLE_COUNT + 1))
    else
        STABLE_COUNT=0
        PREV_COUNT=$COUNT
    fi

    # Show current status
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$TIMESTAMP] Documents in ChromaDB: $COUNT"

    # If count hasn't changed for 30 seconds (3 iterations), consider it stable
    if [ "$STABLE_COUNT" -ge 3 ] && [ "$COUNT" -gt 0 ]; then
        echo ""
        echo "✅ Embedding appears complete - count stable at $COUNT documents"
        echo ""
        echo "Collection details:"
        docker exec chatbot-app python -c "
import chromadb
client = chromadb.HttpClient(host='chromadb', port=8000)
collection = client.get_collection('chatbot_knowledge')
print(f'  Total documents: {collection.count()}')
print(f'  Collection name: {collection.name}')
" 2>/dev/null
        break
    fi

    sleep 10
done
