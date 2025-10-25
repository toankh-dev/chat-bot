"""
Build vector index from S3 data into ChromaDB
"""

import asyncio
import boto3
import json
import logging
import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from vector_store.chromadb_client import VectorStoreClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_s3_documents(bucket_name: str) -> list:
    """
    Fetch all documents from S3

    Args:
        bucket_name: S3 bucket name

    Returns:
        List of documents
    """

    endpoint_url = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")

    s3 = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        region_name=os.getenv("AWS_DEFAULT_REGION", "ap-southeast-1")
    )

    logger.info(f"Fetching documents from S3 bucket: {bucket_name}")

    documents = []

    try:
        # List all objects in bucket
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name)

        for page in pages:
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                key = obj['Key']

                # Only process JSON files
                if not key.endswith('.json'):
                    continue

                # Download and parse
                try:
                    response = s3.get_object(Bucket=bucket_name, Key=key)
                    content = response['Body'].read()
                    doc = json.loads(content)

                    documents.append(doc)

                except Exception as e:
                    logger.error(f"Error processing {key}: {e}")
                    continue

        logger.info(f"Fetched {len(documents)} documents from S3")
        return documents

    except Exception as e:
        logger.error(f"Error fetching from S3: {e}")
        return []


async def main():
    """Main function"""

    logger.info("=" * 60)
    logger.info("Building Vector Index")
    logger.info("=" * 60)

    # Initialize vector store
    logger.info("\n📚 Connecting to ChromaDB...")

    vector_store = VectorStoreClient(
        host=os.getenv("CHROMADB_HOST", "localhost"),
        port=int(os.getenv("CHROMADB_PORT", "8001")),
        embedding_service_url=os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8002")
    )

    await vector_store.initialize()

    # Fetch documents from S3
    logger.info("\n📦 Fetching documents from S3...")

    bucket_name = os.getenv("S3_BUCKET_NAME", "chatbot-raw-data")
    documents = await fetch_s3_documents(bucket_name)

    if not documents:
        logger.warning("⚠️  No documents found in S3")
        logger.info("\nPlease run: python scripts/run_data_fetcher.py first")
        return 1

    # Add documents to vector store
    logger.info(f"\n🔨 Building vector index for {len(documents)} documents...")

    try:
        added_count = await vector_store.add_documents(documents, batch_size=50)

        logger.info("\n" + "=" * 60)
        logger.info("✅ Vector Index Built Successfully!")
        logger.info("=" * 60)
        logger.info(f"Total documents indexed: {added_count}")

        # Test search
        logger.info("\n🔍 Testing search...")

        results = await vector_store.search("bug", limit=3)

        if results:
            logger.info(f"Found {len(results)} test results")
            logger.info("\nTop result:")
            logger.info(f"  {results[0]['document']['text'][:100]}...")
        else:
            logger.warning("No results found (index may be empty)")

        logger.info("\n🎉 All done! You can now start the chatbot.")
        logger.info("\nNext steps:")
        logger.info("  1. Start the application: docker-compose up app")
        logger.info("  2. Test the chat endpoint:")
        logger.info("     curl -X POST http://localhost:8000/chat \\")
        logger.info("       -H 'Content-Type: application/json' \\")
        logger.info("       -d '{\"message\": \"What are the open bugs?\", \"conversation_id\": \"test-1\"}'")

        return 0

    except Exception as e:
        logger.error(f"\n❌ Error building vector index: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
