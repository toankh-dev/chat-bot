"""
Add summary documents for each Excel sheet to enable counting and overview queries
"""

import sys
import pandas as pd
from pathlib import Path
import json

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def create_summary_documents(excel_file):
    """Create summary documents for each sheet"""

    print(f"Creating summary documents for: {excel_file.name}")

    summaries = []
    excel_data = pd.ExcelFile(excel_file)

    for sheet_name in excel_data.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        # Get basic stats
        total_rows = len(df)
        total_columns = len(df.columns)
        non_empty_rows = df.dropna(how='all').shape[0]

        # Get column info
        columns_info = []
        for col in df.columns:
            non_null = df[col].notna().sum()
            unique_vals = df[col].nunique()
            columns_info.append({
                "name": str(col),
                "non_null_count": int(non_null),
                "unique_values": int(unique_vals)
            })

        # Create summary text
        summary_text = f"""
Sheet Summary: {sheet_name}

Total Rows: {total_rows}
Non-empty Rows: {non_empty_rows}
Total Columns: {total_columns}

Columns:
{chr(10).join([f"- {col['name']}: {col['non_null_count']} non-null values, {col['unique_values']} unique" for col in columns_info[:20]])}

Sample Data (first 3 rows):
{df.head(3).to_string()}

This sheet contains {non_empty_rows} data rows with {total_columns} columns.
""".strip()

        summaries.append({
            "text": summary_text,
            "metadata": {
                "source": "excel_summary",
                "file": excel_file.name,
                "sheet": sheet_name,
                "type": "summary",
                "total_rows": total_rows,
                "non_empty_rows": non_empty_rows,
                "total_columns": total_columns,
                "columns": [c["name"] for c in columns_info]
            }
        })

        print(f"  ✓ {sheet_name}: {non_empty_rows} rows, {total_columns} cols")

    return summaries


def embed_summaries_via_docker(summaries):
    """Embed summary documents via Docker container"""
    import subprocess
    import tempfile
    import os

    print(f"\nEmbedding {len(summaries)} summary documents...")

    # Save to temp file
    temp_dir = tempfile.gettempdir()
    summary_file = os.path.join(temp_dir, "summary_documents.json")

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False)

    # Create embedding script
    script = '''
import sys
import json
import asyncio
import time
sys.path.append("/app")

from embeddings.voyage_client import VoyageEmbeddingProvider
import chromadb

async def main():
    # Load summaries
    with open("/tmp/summary_documents.json", "r", encoding="utf-8") as f:
        summaries = json.load(f)

    print(f"Loaded {len(summaries)} summary documents")

    # Initialize VoyageAI
    voyage = VoyageEmbeddingProvider()
    print("✓ VoyageAI initialized")

    # Connect to ChromaDB
    client = chromadb.HttpClient(host="chromadb", port=8000)
    collection = client.get_or_create_collection(
        name="chatbot_knowledge",
        metadata={"description": "Knowledge base for chatbot"}
    )
    print(f"✓ ChromaDB connected (current: {collection.count()} docs)")

    # Generate embeddings for all summaries at once
    texts = [s["text"] for s in summaries]

    print(f"\\nGenerating embeddings for {len(texts)} summaries...")
    embeddings = await voyage.embed_texts(texts)
    print(f"✓ Generated {len(embeddings)} embeddings")

    # Store in ChromaDB
    ids = [f"summary_{s['metadata']['sheet'].replace(' ', '_')}" for s in summaries]
    metadatas = [s["metadata"] for s in summaries]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    print(f"✓ Stored {len(summaries)} summary documents")
    print(f"✓ New total: {collection.count()} documents")

if __name__ == "__main__":
    asyncio.run(main())
'''

    script_file = os.path.join(temp_dir, "embed_summaries.py")
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script)

    # Copy to container
    print("Copying files to container...")
    subprocess.run(
        ["docker", "cp", summary_file, "chatbot-app:/tmp/summary_documents.json"],
        capture_output=True
    )
    subprocess.run(
        ["docker", "cp", script_file, "chatbot-app:/tmp/embed_summaries.py"],
        capture_output=True
    )

    # Run in container
    print("Running embedding in container...\n")
    result = subprocess.run(
        ["docker", "exec", "chatbot-app", "python", "/tmp/embed_summaries.py"],
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr and "Failed to send telemetry" not in result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode == 0


def main():
    """Main function"""
    print("=" * 60)
    print("ADD SUMMARY DOCUMENTS FOR COUNTING & OVERVIEW")
    print("=" * 60)

    # Find Excel files
    data_dir = Path("embedding-data")
    excel_files = list(data_dir.glob("*.xlsx")) + list(data_dir.glob("*.xls"))

    if not excel_files:
        print(f"\n✗ No Excel files found in {data_dir}")
        return 1

    print(f"\n✓ Found {len(excel_files)} file(s)\n")

    # Create summaries
    all_summaries = []
    for excel_file in excel_files:
        summaries = create_summary_documents(excel_file)
        all_summaries.extend(summaries)

    print(f"\n✓ Created {len(all_summaries)} summary documents")

    # Embed
    if embed_summaries_via_docker(all_summaries):
        print("\n" + "=" * 60)
        print("✅ SUCCESS")
        print("=" * 60)
        print(f"\nAdded {len(all_summaries)} summary documents!")
        print("\nNow you can ask:")
        print('  - "How many rows in 画面一覧 sheet?"')
        print('  - "What columns are in the HOME sheet?"')
        print('  - "Summarize the PRD101 sheet"')
        return 0
    else:
        print("\n✗ Failed to embed summaries")
        return 1


if __name__ == "__main__":
    sys.exit(main())
