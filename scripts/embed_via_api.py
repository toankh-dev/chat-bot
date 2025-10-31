"""
Embed Excel data using the FastAPI app's vector store
This bypasses ChromaDB version issues by using the app's endpoint
"""

import sys
import json
from pathlib import Path

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
        return 0
    else:
        print_section("✗ FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
