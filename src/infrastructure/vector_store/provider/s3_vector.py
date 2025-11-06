from ..base import BaseVectorStore
from typing import List, Any
import boto3
import numpy as np
import uuid
import pickle

class S3VectorStore(BaseVectorStore):
    def __init__(self, bucket_name: str, prefix: str = "vectors/"):
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.s3 = boto3.client("s3")

    def add_vector(self, vector: List[float], metadata: dict) -> str:
        vector_id = str(uuid.uuid4())
        obj = {"vector": np.array(vector), "metadata": metadata}
        data = pickle.dumps(obj)
        key = f"{self.prefix}{vector_id}.pkl"
        self.s3.put_object(Bucket=self.bucket_name, Key=key, Body=data)
        return vector_id

    def query(self, vector: List[float], top_k: int = 5) -> List[Any]:
        # NOTE: This is a simple brute-force search for demonstration.
        # For production, use a more efficient method or index.
        import io
        from scipy.spatial.distance import cosine
        response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=self.prefix)
        results = []
        if "Contents" in response:
            for obj in response["Contents"]:
                key = obj["Key"]
                file_obj = self.s3.get_object(Bucket=self.bucket_name, Key=key)
                data = file_obj["Body"].read()
                stored = pickle.loads(data)
                dist = cosine(vector, stored["vector"])
                results.append((key, dist, stored["metadata"]))
            results.sort(key=lambda x: x[1])
            return results[:top_k]
        return []
