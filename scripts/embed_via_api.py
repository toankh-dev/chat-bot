"""
Embed Excel data using the FastAPI app's vector store
This bypasses ChromaDB version issues by using the app's endpoint
"""

import sys
import pandas as pd
import requests
import json
from pathlib import Path
from datetime import datetime

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

API_BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


import pandas as pd
from pathlib import Path
from textwrap import shorten

def process_excel_file(file_path, chunk_size=4000, max_metadata_fields=10, min_text_length=20):
    """
    Extract and enrich documents from an Excel file for ChromaDB ingestion.
    Includes both row-level and sheet-level context.
    """

    print(f"\n📘 Reading Excel file: {file_path}")
    documents = []

    excel_file = pd.ExcelFile(file_path)
    print(f"→ Found {len(excel_file.sheet_names)} sheets")

    for sheet_idx, sheet_name in enumerate(excel_file.sheet_names, 1):
        print(f"\n[{sheet_idx}/{len(excel_file.sheet_names)}] Processing sheet: '{sheet_name}'")

        df = pd.read_excel(file_path, sheet_name=sheet_name)
        if df.empty:
            print("  ⚠️ Sheet is empty, skipping.")
            continue

        row_docs = 0
        all_texts = []  # để tạo sheet-level summary sau

        # ---- 1️⃣ Row-level documents ----
        for row in df.itertuples(index=True):
            text_parts = []
            metadata = {
                "source": "excel",
                "file": Path(file_path).name,
                "sheet": sheet_name,
                "row": row.Index + 2,  # dòng thật trong Excel
                "type": "row"
            }

            # duyệt từng cột nhanh hơn qua df.columns
            for col in df.columns:
                value = getattr(row, col)
                if pd.notna(value) and str(value).strip():
                    text_parts.append(f"{col}: {value}")

                    # thêm metadata hạn chế
                    if len(metadata) - 5 < max_metadata_fields:
                        clean_col = str(col).replace(" ", "_").lower()[:50]
                        metadata[clean_col] = shorten(str(value), width=100, placeholder="...")

            if text_parts:
                text = " | ".join(text_parts)
                if len(text) >= min_text_length:
                    if len(text) > chunk_size:
                        text = text[:chunk_size] + "..."
                    documents.append({
                        "text": text,
                        "metadata": metadata
                    })
                    row_docs += 1
                    all_texts.append(text)

        print(f"  ✔ Created {row_docs} row-level docs")

        # ---- 2️⃣ Sheet-level summary document ----
        if all_texts:
            full_text = "\n".join(all_texts)
            # chia nhỏ theo chunk_size để tránh quá dài
            chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
            for j, chunk in enumerate(chunks, 1):
                documents.append({
                    "text": chunk,
                    "metadata": {
                        "source": "excel",
                        "file": Path(file_path).name,
                        "sheet": sheet_name,
                        "type": "sheet_summary",
                        "chunk": j
                    }
                })
            print(f"  ➕ Added {len(chunks)} sheet-level summary chunks")

    print(f"\n✅ Total {len(documents)} documents extracted from {len(excel_file.sheet_names)} sheets.")
    return documents


def embed_via_docker(documents, batch_size=10):
    """Embed documents using Docker container's Python environment"""
    print_section("Embedding via Docker Container")

    # Create a temporary Python script
    script = '''
        import sys
        import json
        import asyncio
        import time
        sys.path.append("/app")

        from embeddings.voyage_client import VoyageEmbeddingProvider
        from embeddings.chunk_router import chunk_data
        import chromadb

        async def main():
            # Load documents
            with open("/tmp/documents.json", "r", encoding="utf-8") as f:
                documents = json.load(f)

            print(f"Loaded {len(documents)} documents")

            # ===== CHUNKING LOGIC =====
            print("\\n🔀 Chunking documents...")
            chunked_documents = []
            for doc in documents:
                source_type = doc["metadata"].get("source", "text")
                # Chunk based on source type
                chunks = chunk_data(source_type, doc["text"])
                for chunk in chunks:
                    # Merge original metadata with chunk metadata
                    merged_metadata = {**doc["metadata"], **chunk["metadata"]}
                    chunked_documents.append({
                        "text": chunk["text"],
                        "metadata": merged_metadata
                    })
            print(f"✓ Chunked into {len(chunked_documents)} pieces (from {len(documents)} original docs)")

            # Initialize VoyageAI
            voyage = VoyageEmbeddingProvider()
            print(f"✓ VoyageAI initialized")

            # Connect to ChromaDB
            client = chromadb.HttpClient(host="chromadb", port=8000)
            collection = client.get_or_create_collection(
                name="chatbot_knowledge",
                metadata={"description": "Knowledge base for chatbot"}
            )
            print(f"✓ ChromaDB connected (current count: {collection.count()})")

            # Process in batches with rate limiting
            # VoyageAI free tier: 3 RPM, so wait 20 seconds between requests
            batch_size = 50
            total = len(chunked_documents)
            wait_time = 20  # seconds between batches

            for i in range(0, total, batch_size):
                batch = chunked_documents[i:i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (total - 1) // batch_size + 1

                print(f"\\nBatch {batch_num}/{total_batches}: Processing {len(batch)} documents...")

                # Extract texts
                texts = [doc["text"] for doc in batch]

                try:
                    # Generate embeddings
                    embeddings = await voyage.embed_texts(texts)
                    print(f"  ✓ Generated {len(embeddings)} embeddings")

                    # Store in ChromaDB
                    ids = [f"doc_{i + j}" for j in range(len(batch))]
                    metadatas = [doc["metadata"] for doc in batch]

                    collection.add(
                        ids=ids,
                        embeddings=embeddings,
                        documents=texts,
                        metadatas=metadatas
                    )
                    print(f"  ✓ Stored in ChromaDB (total: {collection.count()})")

                    # Wait to avoid rate limit (except for last batch)
                    if batch_num < total_batches:
                        print(f"  ⏳ Waiting {wait_time}s for rate limit...")
                        time.sleep(wait_time)

                except Exception as e:
                    print(f"  ✗ Error: {e}")
                    print(f"  Continuing from where we left off...")
                    break

            print(f"\\n✅ Total documents in collection: {collection.count()}")

        if __name__ == "__main__":
            asyncio.run(main())
    '''

    # Save documents to JSON
    import tempfile
    import os

    temp_dir = tempfile.gettempdir()
    doc_file = os.path.join(temp_dir, "documents.json")
    script_file = os.path.join(temp_dir, "embed_script.py")

    print(f"Saving {len(documents)} documents to temp file...")
    with open(doc_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False)

    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script)

    print(f"✓ Saved to {doc_file}")
    print(f"✓ Saved script to {script_file}")

    # Copy files to container and run
    print("\nCopying files to Docker container...")

    import subprocess

    # Copy documents
    result = subprocess.run(
        ["docker", "cp", doc_file, "chatbot-app:/tmp/documents.json"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"✗ Failed to copy documents: {result.stderr}")
        return False
    print("✓ Copied documents.json")

    # Copy script
    result = subprocess.run(
        ["docker", "cp", script_file, "chatbot-app:/tmp/embed_script.py"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"✗ Failed to copy script: {result.stderr}")
        return False
    print("✓ Copied embed_script.py")

    # Run the script in container
    print("\n🚀 Running embedding in Docker container...")
    print("This will take several minutes...\n")

    result = subprocess.run(
        ["docker", "exec", "chatbot-app", "python", "/tmp/embed_script.py"],
        capture_output=True,
        text=True
    )

    # Print output
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode == 0:
        print("\n✅ Embedding completed successfully!")
        return True
    else:
        print(f"\n✗ Embedding failed")
        return False


def main():
    """Main function"""
    print_section("EXCEL EMBEDDING VIA DOCKER")

    # Find Excel files
    data_dir = Path("embedding-data")
    excel_files = list(data_dir.glob("*.xlsx")) + list(data_dir.glob("*.xls"))

    if not excel_files:
        print(f"\n✗ No Excel files in {data_dir}")
        return 1

    print(f"\n✓ Found {len(excel_files)} file(s)")

    # Process
    all_documents = []
    for excel_file in excel_files:
        print_section(f"Processing: {excel_file.name}")
        documents = process_excel_file(excel_file)
        if documents:
            all_documents.extend(documents)

    if not all_documents:
        print("\n✗ No documents extracted")
        return 1

    print(f"\n✓ Total: {len(all_documents)} documents ready to embed")

    # Embed via Docker
    if embed_via_docker(all_documents):
        print_section("✅ SUCCESS")
        print(f"\nEmbedded {len(all_documents)} documents!")
        print("\nTest with:")
        print("  curl -X POST http://localhost:8000/search \\")
        print("    -H 'Content-Type: application/json' \\")
        print("    -d '{\"query\": \"画面一覧\", \"limit\": 5}'")
        return 0
    else:
        print_section("✗ FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
