"""
Mock implementation of S3FileStorageService for testing.
"""

class S3FileStorageServiceMock:
    """Mock S3 storage service that keeps files in memory."""
    def __init__(self):
        self.files = {}

    async def put_file(self, key: str, data: bytes):
        """Store a file in memory."""
        self.files[key] = data

    async def get_file(self, key: str) -> bytes:
        """Get a file from memory."""
        return self.files[key]

    async def delete_file(self, key: str):
        """Delete a file from memory."""
        if key in self.files:
            del self.files[key]