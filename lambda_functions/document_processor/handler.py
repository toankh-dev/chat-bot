"""
Lambda Function: Document Processor
Processes documents from S3, chunks them, generates embeddings, and indexes in OpenSearch
"""

import json
import os
import sys
import logging
import hashlib
from typing import Dict, List, Any, Optional
from urllib.parse import unquote_plus
import re

# Add common directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

from bedrock_client import BedrockClient
from opensearch_client import OpenSearchVectorClient
from s3_client import S3Client

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Global clients (initialized once per Lambda container)
bedrock_client = None
opensearch_client = None
s3_client = None

# Document processing configuration
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))
MAX_DOCUMENT_SIZE_MB = int(os.getenv('MAX_DOCUMENT_SIZE_MB', '10'))

def initialize_clients():
    """Initialize AWS clients (reused across invocations)"""
    global bedrock_client, opensearch_client, s3_client

    if bedrock_client is None:
        logger.info("Initializing Bedrock client")
        bedrock_client = BedrockClient(
            region=os.getenv('AWS_REGION'),
            embed_model_id=os.getenv('BEDROCK_EMBED_MODEL_ID')
        )

    if opensearch_client is None:
        logger.info("Initializing OpenSearch client")
        opensearch_client = OpenSearchVectorClient(
            collection_endpoint=os.getenv('OPENSEARCH_ENDPOINT'),
            collection_id=os.getenv('OPENSEARCH_COLLECTION_ID'),
            index_name=os.getenv('OPENSEARCH_INDEX_NAME', 'knowledge_base'),
            region=os.getenv('AWS_REGION')
        )

    if s3_client is None:
        logger.info("Initializing S3 client")
        s3_client = S3Client(
            region=os.getenv('AWS_REGION')
        )

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for document processing

    Args:
        event: S3 event notification or EventBridge event
        context: Lambda context

    Returns:
        Processing result
    """
    try:
        # Initialize clients on cold start
        if bedrock_client is None or opensearch_client is None or s3_client is None:
            initialize_clients()

        # Parse S3 event
        if 'Records' in event:
            # S3 event notification
            results = []
            for record in event['Records']:
                result = process_s3_event(record)
                results.append(result)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Documents processed successfully',
                    'results': results
                })
            }
        else:
            # Direct invocation or EventBridge event
            bucket = event.get('bucket')
            key = event.get('key')

            if not bucket or not key:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Missing required parameters: bucket, key'})
                }

            result = process_document(bucket, key)
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }

    except Exception as e:
        logger.error(f"Error in document processing: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }

def process_s3_event(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single S3 event record

    Args:
        record: S3 event record

    Returns:
        Processing result
    """
    try:
        # Extract S3 information
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        size = record['s3']['object']['size']

        logger.info(f"Processing document: s3://{bucket}/{key} (size: {size} bytes)")

        # Check file size
        if size > MAX_DOCUMENT_SIZE_MB * 1024 * 1024:
            logger.warning(f"Document too large: {size} bytes (max: {MAX_DOCUMENT_SIZE_MB}MB)")
            return {
                'bucket': bucket,
                'key': key,
                'status': 'skipped',
                'reason': f'Document exceeds maximum size of {MAX_DOCUMENT_SIZE_MB}MB'
            }

        return process_document(bucket, key)

    except Exception as e:
        logger.error(f"Error processing S3 event: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }

def process_document(bucket: str, key: str) -> Dict[str, Any]:
    """
    Process a document: download, chunk, embed, and index

    Args:
        bucket: S3 bucket name
        key: S3 object key

    Returns:
        Processing result
    """
    try:
        # Download document from S3
        logger.info(f"Downloading document from s3://{bucket}/{key}")
        document_content = s3_client.get_object(key=key, bucket=bucket)

        if not document_content:
            logger.error("Failed to download document")
            return {
                'bucket': bucket,
                'key': key,
                'status': 'error',
                'error': 'Failed to download document from S3'
            }

        # Convert bytes to string
        try:
            text = document_content.decode('utf-8')
        except UnicodeDecodeError:
            logger.error("Document is not UTF-8 encoded")
            return {
                'bucket': bucket,
                'key': key,
                'status': 'error',
                'error': 'Document encoding not supported (only UTF-8)'
            }

        logger.info(f"Document downloaded: {len(text)} characters")

        # Extract metadata
        metadata = {
            'source': f's3://{bucket}/{key}',
            'bucket': bucket,
            'key': key,
            'file_name': os.path.basename(key),
            'file_extension': os.path.splitext(key)[1].lower(),
            'processed_at': None  # Will be set by OpenSearch
        }

        # Chunk document
        logger.info("Chunking document")
        chunks = chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
        logger.info(f"Created {len(chunks)} chunks")

        # Generate embeddings for all chunks
        logger.info("Generating embeddings")
        embeddings = bedrock_client.generate_embeddings(chunks)

        if not embeddings or len(embeddings) != len(chunks):
            logger.error(f"Embedding generation failed: expected {len(chunks)}, got {len(embeddings)}")
            return {
                'bucket': bucket,
                'key': key,
                'status': 'error',
                'error': 'Failed to generate embeddings'
            }

        logger.info(f"Generated {len(embeddings)} embeddings")

        # Index chunks in OpenSearch
        logger.info("Indexing chunks in OpenSearch")
        indexed_count = 0
        failed_count = 0

        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            # Generate unique ID for chunk
            chunk_id = generate_chunk_id(bucket, key, i)

            # Create chunk metadata
            chunk_metadata = {
                **metadata,
                'chunk_index': i,
                'chunk_count': len(chunks)
            }

            try:
                # Index in OpenSearch
                opensearch_client.index_document(
                    doc_id=chunk_id,
                    text=chunk_text,
                    embedding=embedding,
                    metadata=chunk_metadata
                )
                indexed_count += 1

            except Exception as e:
                logger.error(f"Failed to index chunk {i}: {str(e)}")
                failed_count += 1

        logger.info(f"Indexing complete: {indexed_count} successful, {failed_count} failed")

        return {
            'bucket': bucket,
            'key': key,
            'status': 'success',
            'chunks_created': len(chunks),
            'chunks_indexed': indexed_count,
            'chunks_failed': failed_count
        }

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}", exc_info=True)
        return {
            'bucket': bucket,
            'key': key,
            'status': 'error',
            'error': str(e)
        }

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Chunk text into smaller pieces with overlap

    Args:
        text: Input text
        chunk_size: Size of each chunk in characters
        overlap: Overlap between chunks in characters

    Returns:
        List of text chunks
    """
    # Clean text
    text = clean_text(text)

    # Split into sentences (simple approach)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        sentence_size = len(sentence)

        # If adding this sentence would exceed chunk size
        if current_size + sentence_size > chunk_size and current_chunk:
            # Save current chunk
            chunks.append(' '.join(current_chunk))

            # Start new chunk with overlap
            # Keep last few sentences for overlap
            overlap_sentences = []
            overlap_size = 0
            for s in reversed(current_chunk):
                if overlap_size + len(s) <= overlap:
                    overlap_sentences.insert(0, s)
                    overlap_size += len(s)
                else:
                    break

            current_chunk = overlap_sentences
            current_size = overlap_size

        # Add sentence to current chunk
        current_chunk.append(sentence)
        current_size += sentence_size

    # Add final chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and special characters

    Args:
        text: Input text

    Returns:
        Cleaned text
    """
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text

def generate_chunk_id(bucket: str, key: str, chunk_index: int) -> str:
    """
    Generate a unique ID for a document chunk

    Args:
        bucket: S3 bucket name
        key: S3 object key
        chunk_index: Index of the chunk

    Returns:
        Unique chunk ID
    """
    # Create hash of bucket + key
    content = f"{bucket}/{key}"
    hash_hex = hashlib.sha256(content.encode()).hexdigest()[:16]

    return f"{hash_hex}_{chunk_index}"

# Example usage for testing
if __name__ == '__main__':
    # Test event (S3 event notification)
    test_event = {
        'Records': [
            {
                's3': {
                    'bucket': {'name': 'test-bucket'},
                    'object': {
                        'key': 'documents/test.txt',
                        'size': 1024
                    }
                }
            }
        ]
    }

    # Mock context
    class MockContext:
        def __init__(self):
            self.function_name = 'document-processor'
            self.memory_limit_in_mb = 2048
            self.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:document-processor'
            self.aws_request_id = 'test-request-id'

    response = handler(test_event, MockContext())
    print(json.dumps(response, indent=2))
