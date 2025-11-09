import boto3
from typing import BinaryIO, Optional
from botocore.exceptions import ClientError
from shared.interfaces.services.storage.file_storage_service import IFileStorageService
from core.config import settings
from core.logger import logger

class S3FileStorageService(IFileStorageService):
    """S3 implementation of file storage service."""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    async def upload_file(
        self, 
        file_content: BinaryIO, 
        file_key: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload file to S3.
        
        Args:
            file_content: File content as binary stream
            file_key: S3 key for the file
            content_type: MIME type of the file
        
        Returns:
            S3 key of uploaded file
        
        Raises:
            Exception: If upload fails
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            # Read file content
            file_content.seek(0)
            file_data = file_content.read()
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_data,
                **extra_args
            )
            
            logger.info(f"Successfully uploaded file to S3: {file_key}")
            return file_key
            
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise Exception(f"S3 upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {e}")
            raise Exception(f"Upload failed: {str(e)}")
    
    async def delete_file(self, file_key: str) -> bool:
        """
        Delete file from S3.
        
        Args:
            file_key: S3 key of the file to delete
        
        Returns:
            True if deletion successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            logger.info(f"Successfully deleted file from S3: {file_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during S3 deletion: {e}")
            return False
    
    async def generate_presigned_url(
        self, 
        file_key: str, 
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for file access.
        
        Args:
            file_key: S3 key of the file
            expiration: URL expiration time in seconds
        
        Returns:
            Presigned URL or None if generation fails
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    async def file_exists(self, file_key: str) -> bool:
        """
        Check if file exists in S3.
        
        Args:
            file_key: S3 key of the file
        
        Returns:
            True if file exists
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"Error checking file existence: {e}")
                return False

    async def get_file(self, file_key: str) -> bytes:
        """
        Get file content from S3.
        
        Args:
            file_key: S3 key of the file to get
        
        Returns:
            File content as bytes
            
        Raises:
            Exception: If download fails
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            file_content = response['Body'].read()
            logger.info(f"Successfully downloaded file from S3: {file_key}")
            return file_content
            
        except ClientError as e:
            logger.error(f"Failed to download file from S3: {e}")
            raise Exception(f"S3 download failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during S3 download: {e}")
            raise Exception(f"Download failed: {str(e)}")