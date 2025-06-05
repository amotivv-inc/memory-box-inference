"""Security utilities for JWT validation and API key encryption"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import string
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# Initialize Fernet cipher
fernet = Fernet(settings.encryption_key.encode())


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for storage"""
    return fernet.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key for use"""
    return fernet.decrypt(encrypted_key.encode()).decode()


def generate_synthetic_key() -> str:
    """Generate a synthetic API key"""
    # Generate a secure random string
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(48))
    return f"sk-proxy-{random_part}"


def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Verify JWT token and return the payload
    
    Returns:
        Dict containing the JWT claims
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check if token is expired (jose handles this, but being explicit)
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except JWTError as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_organization(
    token_payload: Dict[str, Any] = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Get the current organization from the JWT token
    
    Returns:
        Dict containing organization_id and org_name
    """
    organization_id = token_payload.get("sub")
    org_name = token_payload.get("org_name")
    
    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing organization information"
        )
    
    return {
        "organization_id": organization_id,
        "org_name": org_name
    }


def create_jwt_token(organization_id: str, org_name: str) -> str:
    """
    Create a JWT token for an organization
    
    Args:
        organization_id: UUID of the organization
        org_name: Name of the organization
        
    Returns:
        Encoded JWT token
    """
    # Token expiration
    expire = datetime.utcnow() + timedelta(days=settings.jwt_expiration_days)
    
    # Token payload
    payload = {
        "sub": organization_id,  # Subject is the organization ID
        "org_name": org_name,
        "iat": datetime.utcnow(),
        "exp": expire
    }
    
    # Create token
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return token
