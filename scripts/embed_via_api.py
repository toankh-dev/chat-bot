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


def embed_via_docker(excel_files, batch_size=10):
    """Embed Excel files using Docker container's Python environment with chunking"""
    print_section("Embedding via Docker Container")

    # Create a temporary Python script that processes Excel files directly
    script = '''import sys
import json
import asyncio
import time
sys.path.append("/app")

from embeddings.voyage_client import VoyageEmbeddingProvider
from embeddings.chunk_router import chunk_excel
import chromadb

async def main():
    # Load Excel file paths
    with open("/tmp/excel_files.json", "r", encoding="utf-8") as f:
        excel_files = json.load(f)

    print(f"Processing {len(excel_files)} Excel file(s)")

    # ===== CHUNKING EXCEL FILES =====
    print("\\n🔀 Chunking Excel files using chunk_router...")
    all_chunks = []

    for excel_path in excel_files:
        print(f"\\n📘 Chunking: {excel_path}")
        try:
            # Use chunk_excel from chunk_router
            chunks = chunk_excel(excel_path)
            print(f"  ✓ Created {len(chunks)} chunks")
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue

    print(f"\\n✅ Total chunks: {len(all_chunks)}")

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
    total = len(all_chunks)
    wait_time = 20  # seconds between batches

    for i in range(0, total, batch_size):
        batch = all_chunks[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total - 1) // batch_size + 1

        print(f"\\nBatch {batch_num}/{total_batches}: Processing {len(batch)} chunks...")

        # Extract texts
        texts = [chunk["text"] for chunk in batch]

        try:
            # Generate embeddings
            embeddings = await voyage.embed_texts(texts)
            print(f"  ✓ Generated {len(embeddings)} embeddings")

            # Store in ChromaDB with unique IDs
            import time as time_module
            timestamp = int(time_module.time() * 1000)
            ids = [f"chunk_{timestamp}_{i + j}" for j in range(len(batch))]
            metadatas = [chunk["metadata"] for chunk in batch]

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
            continue

    print(f"\\n✅ Total documents in collection: {collection.count()}")

if __name__ == "__main__":
    asyncio.run(main())
'''

    # Save Excel file paths to JSON
    import tempfile
    import os
    import subprocess

    temp_dir = tempfile.gettempdir()
    excel_list_file = os.path.join(temp_dir, "excel_files.json")
    script_file = os.path.join(temp_dir, "embed_script.py")

    # Convert Excel file paths to strings (inside container paths)
    excel_paths_in_container = [f"/tmp/{Path(f).name}" for f in excel_files]

    print(f"Preparing {len(excel_files)} Excel file(s)...")
    with open(excel_list_file, "w", encoding="utf-8") as f:
        json.dump(excel_paths_in_container, f, ensure_ascii=False)

    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script)

    print(f"✓ Saved file list to {excel_list_file}")
    print(f"✓ Saved script to {script_file}")

    # Copy Excel files and script to container
    print("\nCopying files to Docker container...")

    # Copy each Excel file
    for excel_file in excel_files:
        result = subprocess.run(
            ["docker", "cp", str(excel_file), f"chatbot-app:/tmp/{Path(excel_file).name}"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"✗ Failed to copy {excel_file}: {result.stderr}")
            return False
        print(f"✓ Copied {Path(excel_file).name}")

    # Copy Excel file list
    result = subprocess.run(
        ["docker", "cp", excel_list_file, "chatbot-app:/tmp/excel_files.json"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"✗ Failed to copy file list: {result.stderr}")
        return False
    print("✓ Copied excel_files.json")

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
    print_section("EXCEL EMBEDDING VIA DOCKER WITH CHUNKING")

    # Find Excel files
    data_dir = Path("embedding-data")
    excel_files = list(data_dir.glob("*.xlsx")) + list(data_dir.glob("*.xls"))

    if not excel_files:
        print(f"\n✗ No Excel files in {data_dir}")
        return 1

    print(f"\n✓ Found {len(excel_files)} file(s):")
    for f in excel_files:
        print(f"  - {f.name}")

    # Embed via Docker (with chunking inside container using chunk_router)
    print("\n🔀 Chunking will be done inside Docker container using chunk_router.chunk_excel()")

    if embed_via_docker(excel_files):
        print_section("✅ SUCCESS")
        print("\nExcel files have been chunked and embedded!")
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
