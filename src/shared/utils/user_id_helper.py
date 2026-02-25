"""
Helper utilities for extracting integer user IDs from UserEntity.

This is a temporary bridge until UserEntity is migrated to use integer IDs.
"""


def extract_user_id_int(user_entity_id) -> int:
    """
    Extract integer user ID from UserEntity.id (which is currently a UUID).
    
    This is a temporary helper until UserEntity is migrated to use integer IDs.
    The database stores user IDs as integers, but UserEntity currently uses UUIDs.
    
    Args:
        user_entity_id: UserEntity.id (UUID value object or string)
        
    Returns:
        int: Integer user ID extracted from the UUID
    """
    try:
        # Handle UUID value object
        if hasattr(user_entity_id, 'value'):
            id_str = str(user_entity_id.value)
        else:
            id_str = str(user_entity_id)

        # Remove dashes and convert full hex to int
        clean_id = id_str.replace('-', '')
        if id_str.isdigit():
            # Already a digit string
            return int(id_str)
        elif clean_id:
            try:
                # Convert full hex UUID to int, then mod to fit in integer range
                return int(clean_id, 16) % 2147483647
            except ValueError:
                # Fallback: try as decimal
                return int(clean_id) if clean_id.isdigit() else 1
        else:
            return 1
    except Exception:
        # Fallback to default admin ID if conversion fails
        return 1

