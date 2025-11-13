"""
Security helper functions.

Provides utilities for masking sensitive information.
"""


def mask_api_key(api_key: str) -> str:
    """
    Mask API key showing only first 4 and last 4 characters.

    Examples:
        "sk-1234567890abcdef" -> "sk-1****************def"
        "AIzaSyABC123XYZ" -> "AIza***********XYZ"
        "short" -> "short" (too short to mask)

    Args:
        api_key: The API key to mask

    Returns:
        Masked API key string
    """
    if not api_key:
        return ""

    # If key is too short, don't mask it (need at least 9 chars to show 4+4+1 asterisk)
    if len(api_key) <= 8:
        return api_key

    # Get first 4 and last 4 characters
    first_four = api_key[:4]
    last_four = api_key[-4:]

    # Calculate number of asterisks needed
    middle_length = len(api_key) - 8
    asterisks = "*" * max(middle_length, 4)  # Minimum 4 asterisks

    return f"{first_four}{asterisks}{last_four}"


def unmask_api_key_for_storage(masked_key: str) -> str:
    """
    Check if a key is masked (for update operations).

    Args:
        masked_key: Potentially masked API key

    Returns:
        True if the key appears to be masked, False otherwise
    """
    return "*" in masked_key


def is_masked_key(key: str) -> bool:
    """
    Check if an API key is masked.

    Args:
        key: The key to check

    Returns:
        True if masked, False otherwise
    """
    return key and "*" in key
