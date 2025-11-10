"""
Utility functions for embedding services (Infrastructure layer).

These are standalone utility functions that can be used by any embedding
implementation without requiring inheritance.

This approach is cleaner than using a base class because:
1. No multiple inheritance needed
2. Clear separation: utilities vs contracts
3. Easy to test utilities in isolation
4. Can be used by any code, not just classes
"""
from typing import List
from numpy import ndarray
import numpy as np


def numpy_to_list(array: ndarray) -> List[float]:
    """
    Convert numpy array to Python list of floats.

    Args:
        array: Numpy array or list

    Returns:
        List[float]: Python list of floats
    """
    if isinstance(array, ndarray):
        return array.tolist()
    elif isinstance(array, list):
        return array
    else:
        return list(array)


def list_to_numpy(lst: List[float]) -> ndarray:
    """
    Convert Python list to numpy array.

    Args:
        lst: Python list of floats

    Returns:
        ndarray: Numpy array
    """
    return np.array(lst)


def batch_items(items: List[str], batch_size: int = 100) -> List[List[str]]:
    """
    Split items into batches for API processing.

    Args:
        items: List of items to batch
        batch_size: Size of each batch

    Returns:
        List of batches

    Example:
        >>> batch_items(['a', 'b', 'c', 'd'], batch_size=2)
        [['a', 'b'], ['c', 'd']]
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def validate_text_input(text: str) -> None:
    """
    Validate text input before embedding.

    Args:
        text: Text to validate

    Raises:
        ValueError: If text is empty or invalid

    Example:
        >>> validate_text_input("hello")  # OK
        >>> validate_text_input("")  # Raises ValueError
    """
    if not text or not text.strip():
        raise ValueError("Text input cannot be empty")


def normalize_embedding(embedding: List[float]) -> List[float]:
    """
    Normalize embedding vector to unit length.

    Args:
        embedding: Embedding vector

    Returns:
        Normalized embedding vector

    Example:
        >>> normalize_embedding([3.0, 4.0])
        [0.6, 0.8]
    """
    array = np.array(embedding)
    norm = np.linalg.norm(array)
    if norm == 0:
        return embedding
    return (array / norm).tolist()


def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings.

    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector

    Returns:
        Cosine similarity score between -1 and 1

    Example:
        >>> cosine_similarity([1.0, 0.0], [1.0, 0.0])
        1.0
        >>> cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        -1.0
    """
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)

    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))
