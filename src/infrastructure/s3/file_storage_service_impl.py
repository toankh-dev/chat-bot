from shared.interfaces.services.storage.file_storage_service import IFileStorageService
import boto3
from typing import BinaryIO

class S3FileStorageService(IFileStorageService):
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3", region_name=region)
    
    async def upload_file(self, file_content: BinaryIO, s3_key: str, content_type: str) -> str:
        self.s3_client.upload_fileobj(
            file_content,
            self.bucket_name,
            s3_key,
            ExtraArgs={"ContentType": content_type}
        )
        
        return f"s3://{self.bucket_name}/{s3_key}"
    
    async def delete_file(self, s3_key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except Exception:
            return False
    
    async def generate_presigned_url(self, s3_key: str, expires_in: int = 3600) -> str:
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": s3_key},
            ExpiresIn=expires_in
        )