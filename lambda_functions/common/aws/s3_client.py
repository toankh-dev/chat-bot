"""
Amazon S3 Client
Document storage and retrieval
"""

import logging
import os
import json
from typing import List, Dict, Any, Optional, BinaryIO
from pathlib import Path
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from .config import get_settings, AWSClientFactory

logger = logging.getLogger(__name__)


class S3Client:
    """Client for Amazon S3 operations"""

    def __init__(self, bucket_name: str = None, region: str = None, factory: AWSClientFactory = None):
        """
        Initialize S3 client with environment-aware configuration.

        Args:
            bucket_name: Default S3 bucket name (optional, uses settings default)
            region: AWS region (optional, uses settings default)
            factory: AWS client factory (optional, uses global factory)
        """
        self.settings = get_settings()
        self.region = region or self.settings.aws_region
        self.bucket_name = bucket_name or self.settings.documents_bucket
        self.factory = factory or AWSClientFactory()

        # Initialize S3 client and resource using factory
        # Add S3-specific config
        s3_config = Config(
            region_name=self.region,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            signature_version='s3v4'
        )
        self.s3 = self.factory.create_client('s3', self.region, config=s3_config)
        self.s3_resource = self.factory.create_resource('s3', self.region)

        logger.info(f"Initialized S3 client in {self.region} (environment: {self.settings.environment.value})")
        if self.bucket_name:
            logger.info(f"Default bucket: {self.bucket_name}")

    def upload_file(
        self,
        file_path: str,
        key: str,
        bucket: str = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Upload a file to S3

        Args:
            file_path: Local file path
            key: S3 object key
            bucket: S3 bucket (uses default if not provided)
            metadata: Object metadata
            content_type: Content type

        Returns:
            True if successful
        """
        bucket = bucket or self.bucket_name
        if not bucket:
            raise ValueError("Bucket name is required")

        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            if content_type:
                extra_args['ContentType'] = content_type

            # Auto-detect content type if not provided
            if not content_type:
                content_type = self._guess_content_type(file_path)
                if content_type:
                    extra_args['ContentType'] = content_type

            self.s3.upload_file(
                file_path,
                bucket,
                key,
                ExtraArgs=extra_args if extra_args else None
            )

            logger.info(f"Uploaded {file_path} to s3://{bucket}/{key}")
            return True

        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return False

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        key: str,
        bucket: str = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Upload a file object to S3

        Args:
            fileobj: File-like object
            key: S3 object key
            bucket: S3 bucket
            metadata: Object metadata
            content_type: Content type

        Returns:
            True if successful
        """
        bucket = bucket or self.bucket_name
        if not bucket:
            raise ValueError("Bucket name is required")

        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            if content_type:
                extra_args['ContentType'] = content_type

            self.s3.upload_fileobj(
                fileobj,
                bucket,
                key,
                ExtraArgs=extra_args if extra_args else None
            )

            logger.info(f"Uploaded file object to s3://{bucket}/{key}")
            return True

        except Exception as e:
            logger.error(f"Error uploading file object: {e}")
            return False

    def download_file(
        self,
        key: str,
        file_path: str,
        bucket: str = None
    ) -> bool:
        """
        Download a file from S3

        Args:
            key: S3 object key
            file_path: Local file path to save to
            bucket: S3 bucket

        Returns:
            True if successful
        """
        bucket = bucket or self.bucket_name
        if not bucket:
            raise ValueError("Bucket name is required")

        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            self.s3.download_file(bucket, key, file_path)

            logger.info(f"Downloaded s3://{bucket}/{key} to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False

    def get_object(
        self,
        key: str,
        bucket: str = None
    ) -> Optional[bytes]:
        """
        Get object content from S3

        Args:
            key: S3 object key
            bucket: S3 bucket

        Returns:
            Object content as bytes or None
        """
        bucket = bucket or self.bucket_name
        if not bucket:
            raise ValueError("Bucket name is required")

        try:
            response = self.s3.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()

            logger.info(f"Retrieved object s3://{bucket}/{key} ({len(content)} bytes)")
            return content

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"Object not found: s3://{bucket}/{key}")
            else:
                logger.error(f"Error getting object: {e}")
            return None

    def get_object_metadata(
        self,
        key: str,
        bucket: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get object metadata

        Args:
            key: S3 object key
            bucket: S3 bucket

        Returns:
            Object metadata or None
        """
        bucket = bucket or self.bucket_name
        if not bucket:
            raise ValueError("Bucket name is required")

        try:
            response = self.s3.head_object(Bucket=bucket, Key=key)

            metadata = {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {})
            }

            logger.info(f"Retrieved metadata for s3://{bucket}/{key}")
            return metadata

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"Object not found: s3://{bucket}/{key}")
            else:
                logger.error(f"Error getting metadata: {e}")
            return None

    def list_objects(
        self,
        prefix: str = "",
        bucket: str = None,
        max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        List objects in a bucket with a prefix

        Args:
            prefix: Object key prefix
            bucket: S3 bucket
            max_keys: Maximum number of keys to return

        Returns:
            List of object information dictionaries
        """
        bucket = bucket or self.bucket_name
        if not bucket:
            raise ValueError("Bucket name is required")

        try:
            response = self.s3.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })

            logger.info(f"Listed {len(objects)} objects in s3://{bucket}/{prefix}")
            return objects

        except Exception as e:
            logger.error(f"Error listing objects: {e}")
            return []

    def delete_object(
        self,
        key: str,
        bucket: str = None
    ) -> bool:
        """
        Delete an object from S3

        Args:
            key: S3 object key
            bucket: S3 bucket

        Returns:
            True if successful
        """
        bucket = bucket or self.bucket_name
        if not bucket:
            raise ValueError("Bucket name is required")

        try:
            self.s3.delete_object(Bucket=bucket, Key=key)

            logger.info(f"Deleted s3://{bucket}/{key}")
            return True

        except Exception as e:
            logger.error(f"Error deleting object: {e}")
            return False

    def delete_objects(
        self,
        keys: List[str],
        bucket: str = None
    ) -> Dict[str, Any]:
        """
        Delete multiple objects from S3

        Args:
            keys: List of S3 object keys
            bucket: S3 bucket

        Returns:
            Dictionary with deleted and errors lists
        """
        bucket = bucket or self.bucket_name
        if not bucket:
            raise ValueError("Bucket name is required")

        try:
            # Prepare objects for deletion
            objects = [{'Key': key} for key in keys]

            response = self.s3.delete_objects(
                Bucket=bucket,
                Delete={'Objects': objects}
            )

            deleted = response.get('Deleted', [])
            errors = response.get('Errors', [])

            logger.info(f"Deleted {len(deleted)} objects, {len(errors)} errors")

            return {
                'deleted': [obj['Key'] for obj in deleted],
                'errors': errors
            }

        except Exception as e:
            logger.error(f"Error deleting objects: {e}")
            return {'deleted': [], 'errors': [str(e)]}

    def generate_presigned_url(
        self,
        key: str,
        bucket: str = None,
        expiration: int = 3600,
        http_method: str = 'GET'
    ) -> Optional[str]:
        """
        Generate a presigned URL for an object

        Args:
            key: S3 object key
            bucket: S3 bucket
            expiration: URL expiration time in seconds
            http_method: HTTP method (GET or PUT)

        Returns:
            Presigned URL or None
        """
        bucket = bucket or self.bucket_name
        if not bucket:
            raise ValueError("Bucket name is required")

        try:
            client_method = 'get_object' if http_method == 'GET' else 'put_object'

            url = self.s3.generate_presigned_url(
                ClientMethod=client_method,
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )

            logger.info(f"Generated presigned URL for s3://{bucket}/{key}")
            return url

        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None

    def copy_object(
        self,
        source_key: str,
        dest_key: str,
        source_bucket: str = None,
        dest_bucket: str = None
    ) -> bool:
        """
        Copy an object within S3

        Args:
            source_key: Source object key
            dest_key: Destination object key
            source_bucket: Source bucket
            dest_bucket: Destination bucket

        Returns:
            True if successful
        """
        source_bucket = source_bucket or self.bucket_name
        dest_bucket = dest_bucket or self.bucket_name

        if not source_bucket or not dest_bucket:
            raise ValueError("Bucket names are required")

        try:
            copy_source = {'Bucket': source_bucket, 'Key': source_key}

            self.s3.copy_object(
                CopySource=copy_source,
                Bucket=dest_bucket,
                Key=dest_key
            )

            logger.info(f"Copied s3://{source_bucket}/{source_key} to s3://{dest_bucket}/{dest_key}")
            return True

        except Exception as e:
            logger.error(f"Error copying object: {e}")
            return False

    def object_exists(
        self,
        key: str,
        bucket: str = None
    ) -> bool:
        """
        Check if an object exists in S3

        Args:
            key: S3 object key
            bucket: S3 bucket

        Returns:
            True if object exists
        """
        bucket = bucket or self.bucket_name
        if not bucket:
            raise ValueError("Bucket name is required")

        try:
            self.s3.head_object(Bucket=bucket, Key=key)
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"Error checking object existence: {e}")
                raise

    def _guess_content_type(self, file_path: str) -> Optional[str]:
        """Guess content type from file extension"""
        import mimetypes

        content_type, _ = mimetypes.guess_type(file_path)
        return content_type
