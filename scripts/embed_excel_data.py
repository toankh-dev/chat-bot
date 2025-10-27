"""
Embed Excel data into ChromaDB using VoyageAI
This script processes Excel files and stores them in the vector database
"""

import os
import sys
import pandas as pd
import requests
import json
from datetime import datetime
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
VOYAGE_MODEL = os.getenv("VOYAGE_MODEL", "voyage-2")
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = os.getenv("CHROMADB_PORT", "8001")


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def generate_embeddings(texts, batch_size=50):
    """
    Generate embeddings using VoyageAI API

    Args:
        texts: List of texts to embed
        batch_size: Process in batches to avoid token limits

    Returns:
        List of embeddings
    """
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"  Processing batch {i//batch_size + 1} ({len(batch)} texts)...")

        try:
            response = requests.post(
                "https://api.voyageai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {VOYAGE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": batch,
                    "model": VOYAGE_MODEL
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                embeddings = [item["embedding"] for item in result["data"]]
                all_embeddings.extend(embeddings)
                print(f"  ✓ Generated {len(embeddings)} embeddings")
            else:
                print(f"  ✗ API Error: {response.status_code}")
                print(f"    Response: {response.text}")
                return None

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None

    return all_embeddings


def process_excel_file(file_path):
    """
    Process Excel file and extract structured content

    Args:
        file_path: Path to Excel file

    Returns:
        List of documents with text and metadata
    """
    print(f"\nReading Excel file: {file_path}")

    documents = []

    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        print(f"Found {len(excel_file.sheet_names)} sheets")

        for sheet_name in excel_file.sheet_names:
            print(f"\n  Processing sheet: '{sheet_name}'")

            # Read sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")

            # Process each row
            for idx, row in df.iterrows():
                # Create text content from row
                text_parts = []
                metadata = {
                    "source": "excel",
                    "file": os.path.basename(file_path),
                    "sheet": sheet_name,
                    "row": idx + 2,  # +2 for Excel row number (1-indexed + header)
                    "timestamp": datetime.now().isoformat()
                }

                # Combine all non-null values into text
                for col in df.columns:
                    value = row[col]
                    if pd.notna(value) and str(value).strip():
                        # Add column name and value
                        text_parts.append(f"{col}: {value}")

                        # Store first few columns in metadata
                        if len(metadata) < 10:  # Limit metadata size
                            clean_col = str(col).replace(" ", "_").lower()[:50]
                            metadata[clean_col] = str(value)[:100]

                # Create document if we have content
                if text_parts:
                    text = " | ".join(text_parts)

                    # Skip if too short
                    if len(text) < 20:
                        continue

                    # Truncate if too long (VoyageAI has token limits)
                    if len(text) > 8000:
                        text = text[:8000] + "..."

                    documents.append({
                        "id": f"excel_{sheet_name}_{idx}",
                        "text": text,
                        "metadata": metadata
                    })

            print(f"  ✓ Extracted {len([d for d in documents if d['metadata']['sheet'] == sheet_name])} documents from this sheet")

        print(f"\n✓ Total documents extracted: {len(documents)}")
        return documents

    except Exception as e:
        print(f"✗ Error processing Excel file: {e}")
        import traceback
        traceback.print_exc()
        return None


def store_in_chromadb(documents):
    """
    Store documents in ChromaDB with embeddings

    Args:
        documents: List of documents with text and metadata

    Returns:
        True if successful
    """
    print_section("Storing in ChromaDB")

    # Check ChromaDB connection
    try:
        response = requests.get(f"http://{CHROMADB_HOST}:{CHROMADB_PORT}/api/v1/heartbeat", timeout=5)
        if response.status_code == 200:
            print(f"✓ ChromaDB is running at {CHROMADB_HOST}:{CHROMADB_PORT}")
        else:
            print(f"✗ ChromaDB returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to ChromaDB: {e}")
        return False

    # Import chromadb here (optional dependency)
    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError:
        print("✗ chromadb not installed. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "chromadb"])
        import chromadb
        from chromadb.config import Settings

    # Connect to ChromaDB
    print(f"\nConnecting to ChromaDB...")
    client = chromadb.HttpClient(
        host=CHROMADB_HOST,
        port=int(CHROMADB_PORT)
    )

    # Get or create collection
    collection = client.get_or_create_collection(
        name="chatbot_knowledge",
        metadata={"description": "Knowledge base for chatbot"}
    )

    print(f"✓ Collection 'chatbot_knowledge' ready")
    print(f"✓ Current document count: {collection.count()}")

    # Extract texts
    texts = [doc["text"] for doc in documents]

    # Generate embeddings
    print(f"\nGenerating embeddings for {len(texts)} documents...")
    embeddings = generate_embeddings(texts)

    if embeddings is None:
        print("✗ Failed to generate embeddings")
        return False

    # Store in ChromaDB
    print(f"\nStoring documents in ChromaDB...")
    ids = [doc["id"] for doc in documents]
    metadatas = [doc["metadata"] for doc in documents]

    try:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        print(f"✓ Stored {len(documents)} documents")
        print(f"✓ New document count: {collection.count()}")

        return True

    except Exception as e:
        print(f"✗ Error storing in ChromaDB: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search(query="screen layout"):
    """Test search functionality"""
    print_section("Testing Vector Search")

    try:
        import chromadb

        # Connect to ChromaDB
        client = chromadb.HttpClient(
            host=CHROMADB_HOST,
            port=int(CHROMADB_PORT)
        )

        collection = client.get_or_create_collection(name="chatbot_knowledge")

        print(f"Query: '{query}'")

        # Generate query embedding
        query_embeddings = generate_embeddings([query])

        if query_embeddings:
            # Search
            results = collection.query(
                query_embeddings=query_embeddings,
                n_results=3
            )

            print(f"\nTop 3 Results:")
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ), 1):
                similarity = 1.0 - distance
                print(f"\n{i}. Similarity: {similarity:.4f}")
                print(f"   Source: {metadata.get('file', 'unknown')}")
                print(f"   Sheet: {metadata.get('sheet', 'unknown')}")
                print(f"   Row: {metadata.get('row', 'unknown')}")
                print(f"   Content preview: {doc[:100]}...")

            return True

    except Exception as e:
        print(f"✗ Error during search: {e}")
        return False


def main():
    """Main function"""
    print_section("EXCEL DATA EMBEDDING SCRIPT")

    # Check API key
    if not VOYAGE_API_KEY:
        print("\n✗ VOYAGE_API_KEY not found in environment")
        print("Please set it in your .env file")
        return 1

    print(f"\n✓ VoyageAI API Key configured")
    print(f"✓ Model: {VOYAGE_MODEL}")

    # Find Excel files
    data_dir = Path("embedding-data")
    excel_files = list(data_dir.glob("*.xlsx")) + list(data_dir.glob("*.xls"))

    if not excel_files:
        print(f"\n✗ No Excel files found in {data_dir}")
        return 1

    print(f"\n✓ Found {len(excel_files)} Excel file(s):")
    for f in excel_files:
        print(f"  - {f.name} ({f.stat().st_size / 1024 / 1024:.1f} MB)")

    # Process each file
    all_documents = []

    for excel_file in excel_files:
        print_section(f"Processing: {excel_file.name}")

        documents = process_excel_file(excel_file)

        if documents:
            all_documents.extend(documents)
            print(f"✓ Added {len(documents)} documents from {excel_file.name}")
        else:
            print(f"✗ Failed to process {excel_file.name}")

    if not all_documents:
        print("\n✗ No documents extracted")
        return 1

    print(f"\n✓ Total documents to embed: {len(all_documents)}")

    # Ask for confirmation
    response = input("\nProceed with embedding? (y/n): ").lower()
    if response != 'y':
        print("Cancelled by user")
        return 0

    # Store in ChromaDB
    if store_in_chromadb(all_documents):
        # Test search
        test_search()

        print_section("✅ SUCCESS")
        print(f"\nEmbedded {len(all_documents)} documents from {len(excel_files)} Excel file(s)")
        print("\nYou can now query this data via:")
        print("  1. API: curl -X POST http://localhost:8000/search -d '{\"query\":\"your query\"}'")
        print("  2. Chat: curl -X POST http://localhost:8000/chat -d '{\"message\":\"your message\"}'")
        print("  3. Discord bot (if configured)")

        return 0
    else:
        print_section("✗ FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
