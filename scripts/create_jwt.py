#!/usr/bin/env python3
"""Utility script to create JWT tokens for organizations"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import create_jwt_token
from app.config import settings
import argparse
from datetime import datetime, timedelta
import uuid


def main():
    parser = argparse.ArgumentParser(
        description="Create a JWT token for an organization"
    )
    parser.add_argument(
        "--org-id",
        type=str,
        help="Organization ID (UUID). If not provided, a new UUID will be generated"
    )
    parser.add_argument(
        "--org-name",
        type=str,
        required=True,
        help="Organization name"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Token validity in days (default: 365)"
    )
    
    args = parser.parse_args()
    
    # Generate or validate organization ID
    if args.org_id:
        try:
            # Validate UUID format
            uuid.UUID(args.org_id)
            org_id = args.org_id
        except ValueError:
            print(f"Error: Invalid UUID format: {args.org_id}")
            sys.exit(1)
    else:
        org_id = str(uuid.uuid4())
        print(f"Generated Organization ID: {org_id}")
    
    # Override the expiration days in settings temporarily
    original_days = settings.jwt_expiration_days
    settings.jwt_expiration_days = args.days
    
    try:
        # Create the JWT token
        token = create_jwt_token(org_id, args.org_name)
        
        # Calculate expiration
        expiration = datetime.utcnow() + timedelta(days=args.days)
        
        print("\n" + "="*60)
        print("JWT TOKEN CREATED SUCCESSFULLY")
        print("="*60)
        print(f"Organization ID: {org_id}")
        print(f"Organization Name: {args.org_name}")
        print(f"Expires: {expiration.isoformat()}Z")
        print(f"Valid for: {args.days} days")
        print("\nToken:")
        print("-"*60)
        print(token)
        print("-"*60)
        print("\nUse this token in the Authorization header:")
        print(f"Authorization: Bearer {token}")
        print("="*60)
        
    finally:
        # Restore original setting
        settings.jwt_expiration_days = original_days


if __name__ == "__main__":
    main()
