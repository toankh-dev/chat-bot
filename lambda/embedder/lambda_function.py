"""
Lambda function to embed chunked data from S3 into ChromaDB.
Triggered by S3 events when new chunked data is uploaded.

Alternative embedding solutions (since no Bedrock):
1. VoyageAI API (current implementation)
2. Cohere API
3. OpenAI API
4. HuggingFace Inference API
5. Self-hosted models (sentence-transformers)
"""

import json
import boto3
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
import asyncio

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')

# Import embedding modules
try:
    import sys
    sys.path.append('/opt/python')  # Lambda layer path
    from embeddings.voyage_client import VoyageEmbeddingProvider
    import chromadb
    EMBEDDING_AVAILABLE = True
except ImportError as e:
    logger.error(f"Embedding modules not available: {e}")
    EMBEDDING_AVAILABLE = False


async def embed_chunks_async(chunks: List[Dict[str, Any]], voyage: VoyageEmbeddingProvider) -> Dict[str, Any]:
    """
    Embed chunks using VoyageAI

    Args:
        chunks: List of chunks to embed
        voyage: VoyageAI provider

    Returns:
        Dict with embeddings and stats
    """
    stats = {
        'total_chunks': len(chunks),
        'embedded': 0,
        'errors': 0
    }

    embeddings = []

    # Process in batches (VoyageAI rate limits: 3 RPM for free tier)
    batch_size = 50
    total = len(chunks)

    for i in range(0, total, batch_size):
        batch = chunks[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total - 1) // batch_size + 1

        logger.info(f"Batch {batch_num}/{total_batches}: Embedding {len(batch)} chunks...")

        try:
            # Extract texts
            texts = [chunk['text'] for chunk in batch]

            # Generate embeddings
            batch_embeddings = await voyage.embed_texts(texts)
            embeddings.extend(batch_embeddings)
            stats['embedded'] += len(batch_embeddings)

            logger.info(f"  ✓ Generated {len(batch_embeddings)} embeddings")

        except Exception as e:
            logger.error(f"  ✗ Error embedding batch {batch_num}: {e}")
            stats['errors'] += len(batch)
            # Continue with next batch instead of failing completely
            continue

    return {
        'embeddings': embeddings,
        'stats': stats
    }


def store_in_chromadb(chunks: List[Dict[str, Any]], embeddings: List[List[float]],
                     chromadb_host: str, chromadb_port: int) -> Dict[str, int]:
    """
    Store embeddings in ChromaDB

    Args:
        chunks: List of chunks with metadata
        embeddings: List of embedding vectors
        chromadb_host: ChromaDB host
        chromadb_port: ChromaDB port

    Returns:
        Stats about storage
    """
    stats = {
        'total': len(chunks),
        'stored': 0,
        'errors': 0
    }

    try:
        # Connect to ChromaDB
        client = chromadb.HttpClient(host=chromadb_host, port=chromadb_port)
        collection = client.get_or_create_collection(
            name="chatbot_knowledge",
            metadata={"description": "Knowledge base for chatbot"}
        )
        initial_count = collection.count()
        logger.info(f"ChromaDB connected (current count: {initial_count})")

        # Store in batches
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]

            try:
                timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
                ids = [f"chunk_{timestamp}_{i + j}_{os.urandom(2).hex()}" for j in range(len(batch_chunks))]
                texts = [chunk['text'] for chunk in batch_chunks]
                metadatas = [chunk['metadata'] for chunk in batch_chunks]

                collection.add(
                    ids=ids,
                    embeddings=batch_embeddings,
                    documents=texts,
                    metadatas=metadatas
                )
                stats['stored'] += len(batch_chunks)

            except Exception as e:
                logger.error(f"Error storing batch: {e}")
                stats['errors'] += len(batch_chunks)
                continue

        final_count = collection.count()
        logger.info(f"Storage completed: {stats['stored']} stored")
        logger.info(f"ChromaDB count: {initial_count} → {final_count} (+{final_count - initial_count})")

    except Exception as e:
        logger.error(f"Error in store_in_chromadb: {e}")
        raise

    return stats


def lambda_handler(event, context):
    """
    Lambda handler triggered by S3 events

    Event format:
    {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "bucket-name"},
                    "object": {"key": "path/to/batch_xyz.json"}
                }
            }
        ]
    }
    """
    logger.info("Embedder Lambda triggered")
    logger.info(f"Event: {json.dumps(event)}")

    if not EMBEDDING_AVAILABLE:
        logger.error("Embedding modules not available")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Embedding modules not available'})
        }

    try:
        chromadb_host = os.environ.get('CHROMADB_HOST', 'chromadb')
        chromadb_port = int(os.environ.get('CHROMADB_PORT', '8000'))

        # Process each S3 event
        results = []

        for record in event.get('Records', []):
            try:
                # Extract S3 info
                bucket = record['s3']['bucket']['name']
                key = record['s3']['object']['key']

                logger.info(f"Processing s3://{bucket}/{key}")

                # Download batch file from S3
                response = s3_client.get_object(Bucket=bucket, Key=key)
                batch_data = json.loads(response['Body'].read().decode('utf-8'))

                batch_id = batch_data.get('batch_id')
                chunks = batch_data.get('chunks', [])
                source = batch_data.get('source', 'unknown')

                logger.info(f"Batch {batch_id}: {len(chunks)} chunks from {source}")

                if not chunks:
                    logger.warning(f"No chunks in batch {batch_id}")
                    continue

                # Initialize VoyageAI
                voyage = VoyageEmbeddingProvider()
                logger.info(f"VoyageAI initialized with model: {voyage.model}")

                # Embed chunks
                embed_result = asyncio.run(embed_chunks_async(chunks, voyage))
                embeddings = embed_result['embeddings']
                embed_stats = embed_result['stats']

                logger.info(f"Embedded {embed_stats['embedded']}/{embed_stats['total_chunks']} chunks")

                # Store in ChromaDB
                if embeddings:
                    store_stats = store_in_chromadb(chunks, embeddings, chromadb_host, chromadb_port)
                    logger.info(f"Stored {store_stats['stored']}/{store_stats['total']} chunks")

                    results.append({
                        'batch_id': batch_id,
                        'source': source,
                        'chunks': len(chunks),
                        'embedded': embed_stats['embedded'],
                        'stored': store_stats['stored'],
                        'status': 'success'
                    })
                else:
                    logger.error(f"No embeddings generated for batch {batch_id}")
                    results.append({
                        'batch_id': batch_id,
                        'source': source,
                        'status': 'failed',
                        'error': 'No embeddings generated'
                    })

            except Exception as e:
                logger.error(f"Error processing record: {e}", exc_info=True)
                results.append({
                    'status': 'failed',
                    'error': str(e)
                })

        total_embedded = sum(r.get('embedded', 0) for r in results)
        total_stored = sum(r.get('stored', 0) for r in results)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Embedding completed',
                'processed_batches': len(results),
                'total_embedded': total_embedded,
                'total_stored': total_stored,
                'results': results,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Embedding failed', 'error': str(e)})
        }
