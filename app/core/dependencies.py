"""FastAPI dependencies for the API endpoints"""

from fastapi import Header, HTTPException

def validate_user_id(x_user_id: str = Header(..., description="User ID for tracking")) -> str:
    """
    Validate the X-User-ID header
    
    Args:
        x_user_id: User ID from the X-User-ID header
        
    Returns:
        Validated user ID
        
    Raises:
        HTTPException: If user_id is invalid (null, empty, or whitespace-only)
    """
    if not x_user_id or x_user_id.lower() == "null" or x_user_id.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Invalid X-User-ID header: Cannot be null, empty, or whitespace-only"
        )
    return x_user_id
